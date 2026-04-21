"""Tests for the pure update-check logic.

The HTTP call is injected as ``fetcher`` so we never actually hit
GitHub from tests. Network, download, and install paths live on
top of stdlib primitives and are covered only by manual smoke
tests — there is no sensible stdlib-only way to unit-test them.
"""

from semanticTree.updater import (
	CheckResult,
	_find_addon_asset,
	_parse_version,
	check_for_update,
	is_newer,
)


# ---------- version comparison ------------------------------------------------


def test_parse_plain_version():
	assert _parse_version("0.1.0") == (0, 1, 0)


def test_parse_strips_v_prefix():
	assert _parse_version("v0.2.0") == (0, 2, 0)
	assert _parse_version("V1.0.0") == (1, 0, 0)


def test_parse_tolerates_pre_release_suffix():
	assert _parse_version("1.2.3-rc1") == (1, 2, 3)


def test_parse_missing_segment_is_zero():
	assert _parse_version("1.0") == (1, 0)


def test_is_newer_basic():
	assert is_newer("0.2.0", "0.1.0") is True
	assert is_newer("0.1.0", "0.2.0") is False
	assert is_newer("0.1.0", "0.1.0") is False


def test_is_newer_handles_v_prefix():
	assert is_newer("v0.2.0", "0.1.0") is True


def test_is_newer_major_bump():
	assert is_newer("1.0.0", "0.99.99") is True


def test_is_newer_patch_difference():
	assert is_newer("0.1.1", "0.1.0") is True
	assert is_newer("0.1.0", "0.1.1") is False


# ---------- asset selection ---------------------------------------------------


def test_find_asset_picks_the_nvda_addon():
	release = {
		"assets": [
			{"name": "source.zip", "browser_download_url": "http://x/source.zip"},
			{"name": "semanticTree-0.2.0.nvda-addon",
			 "browser_download_url": "http://x/tree.nvda-addon"},
			{"name": "checksums.txt", "browser_download_url": "http://x/checksums.txt"},
		]
	}
	asset = _find_addon_asset(release)
	assert asset is not None
	assert asset["name"] == "semanticTree-0.2.0.nvda-addon"


def test_find_asset_returns_none_when_no_nvda_addon_present():
	release = {"assets": [{"name": "source.zip"}]}
	assert _find_addon_asset(release) is None


def test_find_asset_tolerates_missing_assets_key():
	assert _find_addon_asset({}) is None


# ---------- check_for_update end-to-end (with injected fetcher) ---------------


def _release(tag: str = "v0.2.0", with_asset: bool = True, notes: str = "notes") -> dict:
	return {
		"tag_name": tag,
		"html_url": "https://example.com/release",
		"body": notes,
		"assets": (
			[{
				"name": "semanticTree-0.2.0.nvda-addon",
				"browser_download_url": "https://example.com/semanticTree-0.2.0.nvda-addon",
			}] if with_asset else []
		),
	}


def test_update_available_when_remote_is_newer():
	result = check_for_update(
		"owner", "repo", "0.1.0",
		fetcher=lambda o, r: _release(tag="v0.2.0"),
	)
	assert result.status == "update_available"
	assert result.remote_version == "v0.2.0"
	assert result.local_version == "0.1.0"
	assert result.download_url.endswith(".nvda-addon")
	assert result.release_notes == "notes"


def test_up_to_date_when_equal():
	result = check_for_update(
		"owner", "repo", "0.2.0",
		fetcher=lambda o, r: _release(tag="v0.2.0"),
	)
	assert result.status == "up_to_date"
	assert result.download_url == ""


def test_up_to_date_when_local_is_ahead():
	"""Developer running unreleased bits shouldn't be nagged."""
	result = check_for_update(
		"owner", "repo", "0.3.0-dev",
		fetcher=lambda o, r: _release(tag="v0.2.0"),
	)
	assert result.status == "up_to_date"


def test_no_asset_when_release_has_no_nvda_addon():
	result = check_for_update(
		"owner", "repo", "0.1.0",
		fetcher=lambda o, r: _release(tag="v0.2.0", with_asset=False),
	)
	assert result.status == "no_asset"
	assert result.remote_version == "v0.2.0"
	assert result.release_url == "https://example.com/release"


def test_error_is_returned_when_fetcher_raises():
	def boom(_o, _r):
		raise RuntimeError("offline")
	result = check_for_update("owner", "repo", "0.1.0", fetcher=boom)
	assert result.status == "error"
	assert "offline" in result.error


def test_error_when_release_has_no_tag():
	result = check_for_update(
		"owner", "repo", "0.1.0",
		fetcher=lambda o, r: {"assets": [], "html_url": "https://example.com/release"},
	)
	assert result.status == "error"
	assert "tag" in result.error.lower()


# ---------- CheckResult is a simple dataclass --------------------------------


def test_check_result_defaults_are_empty_strings():
	result = CheckResult(status="up_to_date")
	assert result.local_version == ""
	assert result.remote_version == ""
	assert result.download_url == ""
	assert result.error == ""
