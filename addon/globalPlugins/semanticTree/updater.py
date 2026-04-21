"""Self-update check against GitHub Releases.

Pure-Python, stdlib-only. No ``requests``, no ``packaging`` —
everything here works with ``urllib.request`` + ``json``.

The update flow (triggered by the "Check for Semantic Tree updates…"
menu item in NVDA's Tools menu):

1. :func:`check_for_update` fetches
   ``/repos/{owner}/{repo}/releases/latest`` from the GitHub API.
2. It picks the first ``.nvda-addon`` asset on that release and
   compares the release's tag against the installed version.
3. It returns a :class:`CheckResult` describing one of four states:
   ``up_to_date``, ``update_available``, ``no_asset``, ``error``.
4. The caller (``ui/update.py``) shows a dialog. On install, it
   calls :func:`download_addon` to fetch the asset to a temp path
   and :func:`launch_install` to hand it to NVDA's standard
   add-on installer.

User's ``semanticTree.json`` is never touched by this module. It
lives outside the add-on directory (in NVDA's user config), so the
installer also leaves it alone. Breaking state-file changes are
already handled by ``storage.py``'s schema-version quarantine —
nothing special is needed here.
"""

from __future__ import annotations

import dataclasses
import json
import os
import shutil
import tempfile
import urllib.error
import urllib.request
from typing import Any, Callable


GITHUB_API = "https://api.github.com/repos/{owner}/{repo}/releases/latest"
USER_AGENT = "nvda-semanticTree-updater"
_DEFAULT_TIMEOUT = 10.0
_DOWNLOAD_TIMEOUT = 120.0


# ---------- version comparison ------------------------------------------------


def _parse_version(text: str) -> tuple[int, ...]:
	"""Parse a version string like ``"0.1.0"`` or ``"v0.1.0-rc1"`` into
	a comparable tuple of integers. Trailing non-digits in any segment
	are dropped; missing segments are zero. Robust enough for our
	semver-ish tags; explicitly not a full PEP-440 parser."""
	parts: list[int] = []
	stripped = text.strip().lstrip("vV")
	for segment in stripped.split("."):
		digits = ""
		for char in segment:
			if char.isdigit():
				digits += char
			else:
				break
		parts.append(int(digits) if digits else 0)
	return tuple(parts)


def is_newer(remote: str, local: str) -> bool:
	return _parse_version(remote) > _parse_version(local)


# ---------- result type -------------------------------------------------------


@dataclasses.dataclass
class CheckResult:
	status: str                      # one of: up_to_date, update_available, no_asset, error
	local_version: str = ""
	remote_version: str = ""
	download_url: str = ""
	release_notes: str = ""
	release_url: str = ""
	error: str = ""


# ---------- GitHub API fetch --------------------------------------------------


def fetch_latest_release(owner: str, repo: str, timeout: float = _DEFAULT_TIMEOUT) -> dict:
	"""Return the JSON body of ``/releases/latest`` for ``owner/repo``.

	Raises :class:`urllib.error.URLError` on network failure, or
	:class:`ValueError` if the response is not a JSON object. The
	caller is expected to wrap this in a ``try``/``except``.
	"""
	url = GITHUB_API.format(owner=owner, repo=repo)
	request = urllib.request.Request(
		url,
		headers={
			"Accept": "application/vnd.github+json",
			"User-Agent": USER_AGENT,
		},
	)
	with urllib.request.urlopen(request, timeout=timeout) as response:
		data = json.load(response)
	if not isinstance(data, dict):
		raise ValueError("GitHub API did not return a JSON object")
	return data


def _find_addon_asset(release: dict) -> dict | None:
	for asset in release.get("assets") or []:
		name = str(asset.get("name") or "")
		if name.endswith(".nvda-addon"):
			return asset
	return None


# ---------- the check --------------------------------------------------------


def check_for_update(
	owner: str,
	repo: str,
	local_version: str,
	fetcher: Callable[[str, str], dict] = fetch_latest_release,
) -> CheckResult:
	"""Return a :class:`CheckResult` describing whether an update is
	available. ``fetcher`` is injectable so tests can stub the HTTP
	call."""
	try:
		release = fetcher(owner, repo)
	except urllib.error.URLError as exc:
		return CheckResult(status="error", local_version=local_version, error=str(exc))
	except (ValueError, json.JSONDecodeError) as exc:
		return CheckResult(status="error", local_version=local_version, error=str(exc))
	except Exception as exc:
		return CheckResult(status="error", local_version=local_version, error=str(exc))

	tag = str(release.get("tag_name") or release.get("name") or "")
	asset = _find_addon_asset(release)
	release_url = str(release.get("html_url") or "")
	body = str(release.get("body") or "")

	if not tag:
		return CheckResult(
			status="error",
			local_version=local_version,
			error="Latest release has no tag name.",
			release_url=release_url,
		)

	if not is_newer(tag, local_version):
		return CheckResult(
			status="up_to_date",
			local_version=local_version,
			remote_version=tag,
			release_notes=body,
			release_url=release_url,
		)

	if asset is None:
		return CheckResult(
			status="no_asset",
			local_version=local_version,
			remote_version=tag,
			release_notes=body,
			release_url=release_url,
		)

	return CheckResult(
		status="update_available",
		local_version=local_version,
		remote_version=tag,
		download_url=str(asset.get("browser_download_url") or ""),
		release_notes=body,
		release_url=release_url,
	)


# ---------- download and install ----------------------------------------------


def download_addon(url: str, dest_dir: str | None = None, timeout: float = _DOWNLOAD_TIMEOUT) -> str:
	"""Download the ``.nvda-addon`` at ``url`` into a fresh temp file
	and return the local path. Caller is responsible for cleanup if
	the install is cancelled."""
	if dest_dir is None:
		dest_dir = tempfile.mkdtemp(prefix="semanticTreeUpdate_")
	else:
		os.makedirs(dest_dir, exist_ok=True)
	filename = os.path.basename(url.rstrip("/")) or "semanticTree.nvda-addon"
	if not filename.endswith(".nvda-addon"):
		filename = "semanticTree.nvda-addon"
	dest = os.path.join(dest_dir, filename)

	request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
	with urllib.request.urlopen(request, timeout=timeout) as response, open(dest, "wb") as f:
		shutil.copyfileobj(response, f)
	return dest


def launch_install(path: str) -> None:
	"""Hand the downloaded ``.nvda-addon`` to NVDA's standard add-on
	installer. On Windows this uses the registered file association,
	which NVDA sets up at install time, so every NVDA version reaches
	its normal install dialog (with confirmation + restart prompt).
	"""
	if os.name == "nt" and hasattr(os, "startfile"):
		os.startfile(path)  # type: ignore[attr-defined]
	else:
		# Non-Windows: best-effort. Shouldn't happen since NVDA is Windows-only.
		raise RuntimeError("Add-on installation requires Windows")
