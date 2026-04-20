# Contributing to NVDA-retree

Thanks for wanting to help. This document covers the day-to-day
workflow. For *why* the code is shaped the way it is, read
[`docs/developer_guide.md`](docs/developer_guide.md) first.

## Setting up

You only need Python 3.10+ to work on the core and run the tests; NVDA
itself is only required to exercise the plugin end-to-end inside the
screen reader.

```bash
python -m venv .venv
source .venv/bin/activate    # on Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
```

## Day-to-day commands

| Task            | Command                                        |
|-----------------|------------------------------------------------|
| Run tests       | `pytest`                                       |
| Lint            | `ruff check .`                                 |
| Format          | `ruff format .`                                |
| Build add-on    | `scons`  *(writes `semanticTree-X.Y.Z.nvda-addon`)* |
| Stdlib-only run | `python tests/run.py` *(no pytest needed)*     |

The CI workflow runs lint + tests + build on every push and pull
request; releases are published when a `vX.Y.Z` tag is pushed (see
`.github/workflows/release.yml`).

## Code style

* Four-space tabs (the NVDA convention). `ruff format` enforces this.
* Keep the pure-Python core (`tree.py`, `inheritance.py`, `labels.py`,
  `search.py`, `storage.py`, `identity.py`) free of NVDA imports.
  Tests depend on that.
* Prefer a short for-loop over a clever comprehension when it reads
  more naturally.
* Comments are for the *why* of something non-obvious. Let names and
  types carry the *what*.

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
