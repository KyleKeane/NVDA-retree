"""Build the ``semanticTree-<version>.nvda-addon`` package.

A .nvda-addon file is just a zip with ``manifest.ini`` at the root and
the add-on's source tree next to it. This script uses only the Python
standard library so the repository has no third-party build dependency.

Usage:
    python tools/build_addon.py [--output-dir DIR]
"""

from __future__ import annotations

import argparse
import builtins
import fnmatch
import os
import sys
import zipfile


EXCLUDE_PATTERNS = [
	"__pycache__/*",
	"*/__pycache__/*",
	"*.pyc",
	"*.pyo",
	".DS_Store",
]


def _ensure_gettext_builtin() -> None:
	if not hasattr(builtins, "_"):
		builtins._ = lambda s: s  # type: ignore[attr-defined]


def _should_include(archive_path: str, extra_excludes: list[str]) -> bool:
	for pattern in EXCLUDE_PATTERNS + list(extra_excludes):
		if fnmatch.fnmatch(archive_path, pattern):
			return False
	return True


def build(repo_root: str, output_dir: str) -> str:
	_ensure_gettext_builtin()
	sys.path.insert(0, repo_root)
	import buildVars  # noqa: E402 (must follow the gettext shim)

	name = buildVars.addon_info["addon_name"]
	version = buildVars.addon_info["addon_version"]
	extra_excludes = getattr(buildVars, "excludedFiles", [])

	os.makedirs(output_dir, exist_ok=True)
	out_path = os.path.join(output_dir, f"{name}-{version}.nvda-addon")

	manifest = os.path.join(repo_root, "manifest.ini")
	addon_root = os.path.join(repo_root, "addon")

	with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as zf:
		zf.write(manifest, "manifest.ini")
		for root, dirs, files in os.walk(addon_root):
			dirs[:] = sorted(d for d in dirs if d != "__pycache__")
			for filename in sorted(files):
				full = os.path.join(root, filename)
				arc = os.path.relpath(full, addon_root)
				if _should_include(arc.replace(os.sep, "/"), extra_excludes):
					zf.write(full, arc)

	return out_path


def main(argv: list[str] | None = None) -> int:
	parser = argparse.ArgumentParser(description=__doc__)
	parser.add_argument(
		"--output-dir",
		default=".",
		help="Directory to write the .nvda-addon file into (default: repo root).",
	)
	args = parser.parse_args(argv)

	repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
	out = build(repo_root, os.path.abspath(args.output_dir))
	size_kb = os.path.getsize(out) / 1024
	print(f"built {out} ({size_kb:.1f} KB)")
	return 0


if __name__ == "__main__":
	raise SystemExit(main())
