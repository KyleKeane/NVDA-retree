# Contributing to NVDA-retree

Thanks for wanting to help. This document covers the day-to-day
workflow. For *why* the code is shaped the way it is, read
[`docs/developer_guide.md`](docs/developer_guide.md) first.

## Setting up

All you need is Python 3.10+. There are no third-party Python
dependencies — not for tests, not for the build, not for the add-on
at runtime. NVDA itself is only required to exercise the plugin
end-to-end inside the screen reader.

```bash
git clone https://github.com/kylekeane/nvda-retree.git
cd nvda-retree
python tests/run.py
```

That should print `all N green`. If it does, you have everything you
need to work on the project.

## Day-to-day commands

| Task            | Command                                         |
|-----------------|-------------------------------------------------|
| Run tests       | `python tests/run.py`                           |
| Build add-on    | `python tools/build_addon.py`                   |

Both commands use only the Python standard library. CI runs exactly
these two steps on every push and pull request. Releases are published
when a `vX.Y.Z` tag is pushed (see `.github/workflows/release.yml`).

## Code style

* Tabs for indentation (the NVDA convention). Match surrounding code.
* Keep the pure-Python core (`tree.py`, `inheritance.py`, `labels.py`,
  `search.py`, `storage.py`, `identity.py`) free of NVDA imports.
  Tests depend on that.
* Prefer a short for-loop over a clever comprehension when it reads
  more naturally.
* Comments are for the *why* of something non-obvious. Let names and
  types carry the *what*.

## Adding tests

Drop a `test_*.py` file into `tests/`. Top-level functions named
`test_*` will be discovered and run automatically. The
`testing_helpers.raises` context manager (provided by the runner) is
available if you need to assert that a block raises.

## Manual smoke test in NVDA

Automated tests cover the pure-Python core but cannot exercise NVDA's
wx dialogs or live object tree. Before merging any change that touches
`plugin.py`, `navigator.py`, `walker.py`, `identity.py`, or anything
under `ui/`, walk through this checklist inside a real NVDA session:

1. **Install the build.** `python tools/build_addon.py`, then install
   the resulting `.nvda-addon` via NVDA → Tools → Manage add-ons.
   Restart NVDA.
2. **Label a weakly-named object.** Navigate to an object with no name
   or a poor name (e.g. a toolbar's decorative icon). Press
   **NVDA+Ctrl+Shift+L**, type a label, press Enter. NVDA should
   announce "Label saved". Move away and back; the label should be
   announced in place of the default name.
3. **Assign a parent.** Press **NVDA+Ctrl+Shift+A**. The assign dialog
   should open with the current semantic tree visible (or just
   "(top level)" on a fresh install). Arrow-key to a parent, press
   Enter. NVDA should announce "Assigned".
4. **Semantic navigation.** Press **NVDA+Ctrl+Shift+Up/Down/Left/Right**.
   The navigator object should move according to the semantic tree,
   and NVDA's own navigator should follow (confirm with
   **NVDA+Numpad5** / "report current navigator object").
5. **Search.** Press **NVDA+Ctrl+Shift+F**. Start typing; the list
   should narrow in real time. Try facet syntax like `role:button` and
   negation like `-firefox`. Press Enter on a result; navigation
   should jump to that object.
6. **Persistence.** Restart NVDA. Your labels and assignments should
   still be present (check via the search dialog).
7. **Corrupt-state recovery.** Close NVDA. Edit
   `%APPDATA%/nvda/semanticTree.json` to invalid JSON. Start NVDA.
   The add-on should load empty (no crash), and
   `semanticTree.json.corrupt-<timestamp>` should exist next to the
   original path.

If any step fails, file a bug using the template and include the
application you were reading plus relevant NVDA log lines.

## Branches and PRs

* Branch off `main`. Use a short descriptive name,
  e.g. `add-subtree-export`, `fix-search-crash-on-empty`.
* Rebase onto `main` before asking for review.
* PR descriptions should answer three questions: *what*, *why*, and
  *how I tested it*. The PR template nudges you to do this.
* If a change touches behaviour that is covered by tests, update the
  tests. If it is not yet covered, consider adding a test.

## Releasing

1. Update `manifest.ini` and `buildVars.py` to the new version.
2. Add an entry at the top of `CHANGELOG.md`.
3. Open and merge a PR for the above.
4. Tag `main` with `vX.Y.Z`. The release workflow builds the
   `.nvda-addon` and attaches it to a GitHub release.

## Reporting bugs

Use the issue templates. Include an NVDA log, the application you
were reading, and if possible the contents of `semanticTree.json`
from your NVDA config directory.

## Code of conduct

Be kind, be specific, and assume good faith. We follow the spirit of
the [Contributor Covenant](https://www.contributor-covenant.org/).
