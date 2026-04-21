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

A standalone, no-context-required walkthrough lives at
[`docs/smoke_test.md`](docs/smoke_test.md). Hand that file to anyone
you're asking to smoke-test a build — it's written so a first-time
NVDA user can follow it end-to-end with a pass/fail report template
at the bottom.

Short version for contributors:

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

End users discover updates through the **NVDA → Tools → Check for
Semantic Tree updates…** menu item. That menu item hits GitHub's
`/releases/latest` endpoint, reads the tag name, and downloads the
attached `.nvda-addon`. So "shipping a new version" is: publish a
GitHub Release on a `vX.Y.Z` tag with the built `.nvda-addon`
attached. Everything below automates that.

### The rolling `main-latest` build (auto, for testers)

Separately from stable releases, every merge to `main` triggers
the `dev-release` job in `.github/workflows/ci.yml` which builds
a fresh `.nvda-addon` and attaches it to a pre-release tagged
`main-latest`. The tag is force-moved on every push, so the URL
stays stable:

<https://github.com/KyleKeane/NVDA-retree/releases/tag/main-latest>

This is what a tester should install when they want to exercise
the current state of `main` without waiting for a stable release.
The in-NVDA updater intentionally **does not** surface pre-
releases, so normal users only see `vX.Y.Z`.

### Step 1 — pre-flight

Before you start a release:

* `python tests/run.py` prints `all N green`.
* `git status` is clean on `main`; `git pull` is up to date with
  `origin/main`.
* Skim the `[Unreleased]` section of `CHANGELOG.md`. Does the list
  accurately describe every user-visible change going into this
  version?
* If you're not sure what version to bump to, see
  [Step 5 — versioning policy](#step-5--versioning-policy) below.

### Step 2 — the version-bump PR

Open one PR that does exactly three small edits:

1. **`manifest.ini`** — set `version = X.Y.Z`.
2. **`buildVars.py`** — set `"addon_version": "X.Y.Z"`. Bump
   `"addon_lastTestedNVDAVersion"` if you've exercised this build
   against a newer NVDA than the one already listed.
3. **`CHANGELOG.md`** — rename the `## [Unreleased]` heading to
   `## [X.Y.Z] — YYYY-MM-DD`, and add a fresh empty
   `## [Unreleased]` block above it. Leave the bullet content
   alone; it's what users will see as release notes.

Merge when CI is green.

### Step 3 — tag and push

```bash
git checkout main
git pull
git tag vX.Y.Z
git push origin vX.Y.Z
```

The tag push triggers `.github/workflows/release.yml`, which does,
automatically:

1. Verifies the tag's `X.Y.Z` matches `manifest.ini`'s `version`.
   If they don't match, the workflow aborts before building (a
   safety net — usually this only fires if you forgot step 2).
2. Runs the full test suite.
3. Builds `semanticTree-X.Y.Z.nvda-addon` with
   `python tools/build_addon.py`.
4. Publishes a **GitHub Release** on the tag, with the
   `.nvda-addon` attached and release notes auto-generated from
   the commits since the previous release.

Watch the run live on the **Actions** tab of the repo — end-to-end
takes about 60 seconds.

### Step 4 — confirm the user-visible path

* Open
  <https://github.com/KyleKeane/NVDA-retree/releases/latest>.
  It should show the new version tag.
* The release page's **Assets** section must list
  `semanticTree-X.Y.Z.nvda-addon`. If it doesn't, the workflow
  failed halfway; inspect the Actions run, fix the cause, then
  cut a new patch version (don't try to delete or re-push the
  tag — see [Fixing a bad release](#fixing-a-bad-release)).
* On a test NVDA machine that has an older version installed, go
  to **NVDA → Tools → Check for Semantic Tree updates…**. The
  dialog should now offer the new version with your release
  notes. Click **Install now** — NVDA's standard add-on installer
  takes over from there.

### Step 5 — versioning policy

We follow [Semantic Versioning](https://semver.org/):

| Change                                                            | Bump  |
| ----------------------------------------------------------------- | ----- |
| Bug fix, docs-only, internal refactor                             | patch |
| New user-visible feature, new gesture, non-breaking improvement   | minor |
| Breaking UX change, **bumped `SCHEMA_VERSION` in `storage.py`**   | major |

Bumping `SCHEMA_VERSION` is the most important "major" trigger. A
version with a new schema will automatically quarantine users' old
`semanticTree.json` on first load after install (renamed to
`.corrupt-<timestamp>`, warning in the NVDA log, start empty). The
add-on keeps working; the user just loses labels and assignments.
That's acceptable behaviour for a `major`, but a breaking surprise
for a `minor` — hence the rule.

### Fixing a bad release

If the workflow fails, or the published release turns out subtly
wrong, **do not** try to edit or delete the tag. Tags are cached by
clients (including our own updater, and anyone with the existing
`.nvda-addon` already downloaded), and moving them causes
silent-looking bugs.

The correct recovery is:

1. Merge a fix PR into `main`.
2. Cut a new patch version: `X.Y.Z + 1`.
3. Tag `main` with the new version and push.

The next time any user clicks **Check for Semantic Tree updates…**,
they'll be offered the fixed version and skip straight past the
broken one.

### How users experience a release

For reference, the user-side of the flow looks like:

1. Open NVDA → Tools → **Check for Semantic Tree updates…**
2. A "Checking…" indicator flashes briefly.
3. Either: a dialog offering the new version with release notes,
   or an "up to date" message.
4. On **Install now**, NVDA downloads the `.nvda-addon` and hands
   it to its own standard install flow (confirmation, then restart
   prompt).

Users' labels and assignments live in `%APPDATA%\nvda\semanticTree.json`,
outside the add-on directory, so updates never touch them (except
for the schema-version quarantine case described above).

## Reporting bugs

Use the issue templates. Include an NVDA log, the application you
were reading, and if possible the contents of `semanticTree.json`
from your NVDA config directory.

## Code of conduct

Be kind, be specific, and assume good faith. We follow the spirit of
the [Contributor Covenant](https://www.contributor-covenant.org/).
