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

## [0.1.0] — foundation

### Added
- Pure-Python semantic-tree core (`tree`, `inheritance`, `labels`,
  `identity`, `search`, `storage`) with 21 unit tests.
- NVDA global plugin (`plugin.py`) with seven gestures:
  four-way semantic navigation, label, assign, search.
- wx dialogs for labelling, assigning a semantic parent, and
  searching the tree item-chooser style.
- SCons build that produces `semanticTree-0.1.0.nvda-addon`.
- README, developer guide, and bundled in-NVDA help.
