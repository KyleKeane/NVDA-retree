# Changelog

All notable changes to this project will be documented in this file.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
and this project aims to follow [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Fixed (pre-release polish)
- Search dialog: when the picked object has been evicted from the
  walker cache, announce "Could not locate that object on screen any
  more" instead of silently closing.
- `_role_text` (plugin + facets) now prefers `role.displayString` on
  modern NVDA's Role enum, falling back through legacy
  `controlTypes.roleLabels` and finally `str(role)`. Previous code
  produced strings like "Role.BUTTON" on newer NVDA builds.
- Every `gui.runScriptModalDialog` call is wrapped so that any NVDA
  API drift fails gracefully with a spoken message rather than
  crashing the add-on.

### Fixed (pre-release audit round)
- `identity.get_object_id` no longer collapses `indexInParent=0` (first child)
  or `windowHandle=0` into the missing-value sentinel. Typed helpers
  (`_str_of`, `_int_of`) preserve zero and negative values.
- Semantic navigation now re-anchors to NVDA's current navigator object
  on every press, so moving the NVDA navigator with other gestures in
  between ours is no longer ignored.
- The search dialog's **app** facet now reads `obj.appModule.appName`
  (was reading a non-existent `obj.appModuleName` and always returning `""`).
- `inheritance` rewritten so accessibility structure is preserved
  *inside* an assigned subtree. Previously `body > container > link`
  flattened to `body > {container, link}`; now it stays nested.
  `_inherited_descendants` recursion is gone (no recursion-limit risk).
- NVDA's in-add-on help button opens correctly: we now ship a real
  `readme.html` (manifest pointed at `.html` but we were shipping `.md`).
- Assign dialog hides the object being assigned *and its descendants*
  as candidate parents; previously picking a descendant failed with a
  CycleError at commit time.
- `NVDAWalker.search_subtree` uses `collections.deque` for O(1) BFS
  pops (was `list.pop(0)` — O(n²) over 500 nodes).

### Added
- `SemanticTree.explicit_descendants(root_id)` — tree operation used
  by the assign dialog.
- `facets.py` — pure facet extraction split out of the wx-dependent
  search dialog so it is unit-testable.
- 12 more tests: identity edge cases (zero index, zero handle,
  missing attributes), structure-preserving inheritance, facet
  extraction, tree descendants. Total: **51 tests**.

### Added
- Continuous integration (multi-version tests + build) on every push and PR.
- Release workflow: tagging `vX.Y.Z` publishes a GitHub release with the `.nvda-addon` attached.
- Issue and pull-request templates; Dependabot configuration; `SECURITY.md`; `CONTRIBUTING.md`.
- `NVDAWalker.prime_ancestors` and `search_subtree`: populate the
  weakref cache up the ancestor chain and, on resolution miss, do a
  bounded BFS from the window root. `SemanticNavigator` uses the
  latter as its fallback when an explicit assignment points at an
  object not in cache.
- Every script guards against `api.getNavigatorObject()` returning
  `None` and announces a clear message instead of erroring.
- Test suite grew to **39 cases** covering identity, navigator,
  storage-corruption, and search edge cases.
- Manual smoke-test checklist in `CONTRIBUTING.md`.

### Changed
- Build is now `python tools/build_addon.py` (Python stdlib only); SCons removed.
- Test runner is `python tests/run.py` (Python stdlib only); pytest, ruff,
  pyproject.toml, and requirements-dev.txt removed. The project now has
  **zero third-party dependencies** at any stage (runtime, tests, build).
- `identity.get_object_id` walks dotted attribute paths
  (`appModule.appName`, `UIAAutomationId`) so the app component of an
  object ID is actually populated in real NVDA.
- `storage.load` quarantines unreadable or malformed JSON into
  `<path>.corrupt-<timestamp>` and returns empty stores; the add-on
  keeps running on a cold start.
- Role announcements use `controlTypes.roleLabels` when available.

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
