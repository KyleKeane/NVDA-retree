# Changelog

All notable changes to this project will be documented in this file.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
and this project aims to follow [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added
- Continuous integration (lint, multi-version pytest, build) on every push and PR.
- Release workflow: tagging `vX.Y.Z` publishes a GitHub release with the `.nvda-addon` attached.
- `pyproject.toml` with ruff + pytest configuration.
- Issue and pull-request templates; Dependabot configuration; `SECURITY.md`; `CONTRIBUTING.md`.

### Changed
- Build is now `python tools/build_addon.py` (Python stdlib only); SCons removed.
- `identity.get_object_id` now walks dotted attribute paths
  (`appModule.appName`, `UIAAutomationId`) so the app component of an
  object ID is actually populated in real NVDA.
- `storage.load` quarantines unreadable or malformed JSON into
  `<path>.corrupt-<timestamp>` and returns empty stores; the add-on
  keeps running on a cold start.
- Role announcements use `controlTypes.roleLabels` when available.

### Added
- `NVDAWalker.prime_ancestors` and `search_subtree`: populate the
  weakref cache up the ancestor chain and, on resolution miss, do a
  bounded BFS from the window root. `SemanticNavigator` uses the
  latter as its fallback when an explicit assignment points at an
  object not in cache.
- All scripts guard against `api.getNavigatorObject()` returning
  `None` and announce a clear message instead of erroring.
- Test suite grew to 36 cases covering identity, navigator,
  storage-corruption, and search edge cases.

## [0.1.0] — foundation

### Added
- Pure-Python semantic-tree core (`tree`, `inheritance`, `labels`,
  `identity`, `search`, `storage`) with 21 unit tests.
- NVDA global plugin (`plugin.py`) with seven gestures:
  four-way semantic navigation, label, assign, search.
- wx dialogs for labelling, assigning a semantic parent, and
  searching the tree item-chooser style.
- Stdlib build script (`tools/build_addon.py`) that produces `semanticTree-0.1.0.nvda-addon`.
- README, developer guide, and bundled in-NVDA help.
