# Changelog

All notable changes to this project will be documented in this file.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
and this project aims to follow [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added
- `docs/smoke_test.md` — standalone, no-context-required smoke-test
  walkthrough. Hand it to anyone you ask to exercise a build
  end-to-end; it covers install, gesture registration, help file,
  label, assign, four-way navigation, search, persistence across
  restart, and corrupt-state recovery, each with explicit pass/fail
  criteria and a ready-to-fill report template at the end.

### Changed
- Bundled NVDA help is now authored in Markdown
  (`addon/doc/en/readme.md`) and converted to HTML at build time by a
  tiny stdlib-only converter (`tools/md_to_html.py`). The built zip
  ships `readme.html`, so NVDA's in-add-on help button opens cleanly
  in the browser with proper `<h1>` / `<h2>` / `<ul>` / `<li>` /
  `<strong>` tags for browse-mode navigation. The source tree stays
  markdown-friendly for screen-reader authoring. `manifest.ini` and
  `buildVars.py` point at `readme.html` (what the zip contains). 21
  new unit tests cover the converter (headings, bullet lists with
  indented continuation lines, inline bold / italic / code / links,
  HTML escaping, document-title extraction).

## [0.1.0] — foundation

Initial release: a working NVDA add-on with zero third-party
dependencies at runtime, in tests, or at build time.

### Added

- **Pure-Python core**, NVDA-free and fully unit-tested:
  - `tree.py` — explicit `child → parent` assignments with cycle
    detection and `explicit_descendants`.
  - `inheritance.py` — effective parent / children that *preserve*
    accessibility structure inside an assigned subtree. Assigning
    `body` keeps `body > container > link > span` nested, not
    flattened into `{container, link, span}` under `body`.
  - `identity.py` — stable hashable IDs across sessions. Walks
    dotted attribute paths (`appModule.appName`, `UIAAutomationId`);
    typed helpers preserve `indexInParent=0` and `windowHandle=0`.
  - `labels.py` — user-assigned display labels for objects with
    poor automation names.
  - `search.py` — facet matcher (`role:button firefox -notepad`).
  - `storage.py` — atomic JSON save; corrupt files are quarantined
    as `<path>.corrupt-<timestamp>` and the add-on recovers cleanly.
  - `facets.py` — pure facet extraction split out of the wx UI so
    it is unit-testable.

- **NVDA integration layer**:
  - `walker.py` — `AccessWalker` over live NVDAObjects with a
    weakref cache, `prime_ancestors`, and a bounded deque-backed
    `search_subtree` BFS so cold-cache lookups across a restart
    still resolve.
  - `navigator.py` — semantic cursor that re-anchors to NVDA's
    current navigator on every gesture so intervening manual moves
    are respected.
  - `plugin.py` — `GlobalPlugin` with seven `@script` gestures.
    Every script guards `api.getNavigatorObject()` returning
    `None`. Every dialog open is try/except-wrapped for graceful
    degradation on NVDA API drift. `_role_text` tries, in order:
    `obj.roleText`, `role.displayString` (modern enum),
    `controlTypes.roleLabels[role]` (legacy), `str(role)`.

- **wx dialogs** (`ui/`):
  - `label.py` — set or clear a custom label.
  - `assign.py` — pick a semantic parent from a `wx.TreeCtrl`.
    Hides the object being assigned *and its descendants* as
    candidate parents so the user cannot create a cycle.
  - `search.py` — live-filtered `wx.ListBox` item chooser.
    Announces when a picked object has been evicted from cache
    instead of closing silently.

- **Gestures** (all rebindable from Input gestures → Semantic Tree):
  - `NVDA+Ctrl+Shift+Up/Down/Left/Right` — four-way semantic
    navigation (parent / first child / previous / next sibling).
  - `NVDA+Ctrl+Shift+L` — label / relabel.
  - `NVDA+Ctrl+Shift+A` — assign a semantic parent.
  - `NVDA+Ctrl+Shift+F` — search.

- **Build and CI**:
  - `tools/build_addon.py` — stdlib-only script producing
    `semanticTree-0.1.0.nvda-addon`.
  - `tests/run.py` — stdlib-only test runner with filesystem
    auto-discovery (52 tests).
  - GitHub Actions workflow: matrix tests on Python
    3.10 / 3.11 / 3.12 plus the build, on every push and PR.
  - Release workflow: tagging `vX.Y.Z` verifies the manifest
    version matches the tag, runs tests, builds, and publishes a
    GitHub Release with the `.nvda-addon` attached.
  - Dependabot for GitHub Actions updates.

- **Docs**:
  - `README.md` — user-facing overview, features, shortcuts.
  - `docs/local_install.md` — detailed scratchpad and packaged-
    install walkthrough for Windows/NVDA.
  - `docs/developer_guide.md` — architecture and module-by-module
    reference.
  - `CONTRIBUTING.md` — dev setup, day-to-day commands, and a
    seven-step manual smoke-test checklist.
  - `SECURITY.md`, issue / PR templates.
  - `addon/doc/en/readme.html` — bundled in-NVDA help, linked by
    `manifest.ini`.
