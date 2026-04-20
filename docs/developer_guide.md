# Developer guide

This is the "how and why" companion to the README. If you want to add a
feature, fix a bug, or understand why the code is shaped the way it is,
start here.

## Design principles

1. **Separate the data model from NVDA.** Anything that can be written
   as plain Python is. The `tree`, `inheritance`, `labels`, `search`,
   `storage`, and `identity` modules must never import NVDA. That
   boundary is what lets us write fast unit tests and lets new
   contributors reason about the core in a Python REPL.
2. **Store the minimum.** The semantic tree records only the arrows
   the user has drawn (`child_id → parent_id`). Everything else —
   effective parent, effective children, the set of all visible
   objects — is derived on demand. One source of truth, no sync bugs.
3. **Prefer obvious code over clever code.** A short recursive walk,
   a for-loop, and a flat `dict` will outlive any framework. Comments
   are for the *why* of a non-obvious constraint, not a narration.
4. **Every UI surface is a thin view.** The dialogs in `ui/` exist to
   collect keystrokes from the user and to call one or two methods on
   the core. They do not branch on business logic.

## Layout

```
addon/
  globalPlugins/
    semanticTree/
      __init__.py      # package entry point; NVDA-optional
      plugin.py        # GlobalPlugin: gestures + orchestration
      identity.py      # stable ObjectId tuple for an NVDAObject
      tree.py          # SemanticTree: explicit assignments only
      inheritance.py   # effective_parent, effective_children
      labels.py        # LabelStore
      storage.py       # JSON load/save
      search.py        # item-chooser filter
      navigator.py     # semantic cursor; syncs NVDA's navigator
      walker.py        # NVDA-backed AccessWalker impl + obj cache
      ui/
        assign.py      # wx dialog: pick a semantic parent
        label.py       # wx dialog: set a custom label
        search.py      # wx dialog: live-filtered item chooser
docs/
  developer_guide.md
tests/
  fakes.py             # FakeObject / FakeWalker for core tests
  test_*.py            # pytest-style cases
  run.py               # stdlib runner (no pytest dependency)
manifest.ini           # NVDA manifest (used by SCons and by NVDA)
buildVars.py           # SCons build variables
sconstruct             # SCons build (produces .nvda-addon)
```

## The data model

### `SemanticTree` (tree.py)

A thin wrapper around a `dict[ObjectId, Optional[ObjectId]]`. Keys are
children; values are semantic parents (`None` means "semantic root").
The tree enforces two invariants:

* An object has at most one explicit parent (`dict` guarantees this).
* A move must not create a cycle (`_would_cycle` walks up from the
  proposed new parent looking for the child).

That's all. No children list, no ordering, no metadata.

### `effective_parent` / `effective_children` (inheritance.py)

The inheritance rule is one sentence:

> The effective parent of *X* is its explicit parent if any, else the
> nearest ancestor in the accessibility tree that has an explicit
> parent, else none.

`effective_parent` implements exactly that walk. `effective_children`
inverts it: the explicit children first (in insertion order), then a
recursive walk over the accessibility-tree descendants of the parent,
cutting off at any subtree whose root has been explicitly reassigned
elsewhere (so it does not double-count).

This is where inheritance "for any subsequent children objects" comes
from: when the user discovers a new element in an app later, it's an
accessibility-tree descendant of something, and it will inherit its
position automatically without any action.

### `AccessWalker` (inheritance.py)

A tiny `Protocol` that the inheritance logic uses to walk accessibility
objects. It has four methods: `id_of`, `parent_of`, `children_of`,
`object_for_id`. Tests pass in a `FakeWalker`; production passes in
`NVDAWalker` from `walker.py`. This is the seam that keeps NVDA out
of the pure-Python modules.

### `LabelStore` (labels.py)

A plain `dict[ObjectId, str]`. Setting the empty string clears the
entry. Reading a missing entry returns `None` so callers can fall back
to the object's automation name.

### `ObjectId` (identity.py)

A tuple of `(app, windowHandle, windowControlID, role, name,
automationId, indexInParent)`. No single field is strictly stable
(names change, handles get reused), but the *composite* is stable
enough that the same visible element produces the same ID inside a
session and across most restarts. The tuple is hashable so it can be
used as a dict key and serialised to JSON as an array.

If you improve identity in the future (e.g. by using
`uniqueID`/`IA2UniqueID` when available), do it inside
`identity.get_object_id` only. The rest of the code treats `ObjectId`
as opaque.

### `storage.py`

Atomic JSON: writes to `path + ".tmp"`, then `os.replace`s. The file
lives beside NVDA's user config so that uninstalling and reinstalling
the add-on does not nuke a user's carefully-curated tree.

## The NVDA layer

### `plugin.py`

Defines the `GlobalPlugin` class NVDA instantiates on startup. It:

1. Loads state from `storage.load`.
2. Creates a `NVDAWalker` and a `SemanticNavigator`.
3. Declares the seven scripts (`script_semantic_*`, `script_set_label`,
   `script_assign`, `script_search`) with `@script` decorators.
4. On save/commit, calls `storage.save` so changes survive a restart.

Each script is intentionally tiny: anchor the cursor to NVDA's current
navigator if it isn't already, ask `SemanticNavigator` or a dialog to
do the work, report the result with `ui.message`, and call
`sync_nvda_navigator` so NVDA's own cursor follows.

### `walker.py`

The accessibility-tree side of `AccessWalker`, implemented against real
NVDAObjects. Its only non-obvious trick is a `weakref` cache keyed by
`ObjectId`: we need some way to turn an ID back into a live object for
`to_parent`, `to_first_child`, and the search dialog's "jump to"
action. The cache is populated opportunistically every time we see an
object via `remember`, and degrades gracefully: if the object is gone,
the caller falls back to walking the live accessibility parent chain.

### `navigator.py`

Holds the *semantic cursor* — a single NVDA object that represents
"where I am in my semantic tree right now". Moves (`to_parent`,
`to_first_child`, siblings) are computed via `inheritance.*` and then
applied to both this internal cursor and, through
`sync_nvda_navigator`, to NVDA's own navigator. The rest of NVDA has
no idea the semantic tree exists; it just sees the nav cursor move.

## The UI layer

All three dialogs inherit from `wx.Dialog` and are shown through
`gui.runScriptModalDialog`, the standard NVDA helper for modal UI that
plays nicely with NVDA's own message loop.

* `ui/label.py` — one text field; Enter saves, empty string clears.
* `ui/assign.py` — a `wx.TreeCtrl` of currently-assigned objects.
  The user's own child is filtered out so you cannot reparent a node
  under itself (in addition to the cycle check in `SemanticTree`).
* `ui/search.py` — `wx.TextCtrl` above a `wx.ListBox`. `EVT_TEXT`
  re-filters with `search.filter_items`; `EVT_LISTBOX_DCLICK` commits.

Each dialog takes a callback (`on_commit` / `on_pick`) rather than
mutating core state directly. This keeps the UI layer purely
presentational.

## Identity: things to watch for

Identity is the *only* place state can leak across sessions in a way
that silently breaks assignments. If a user reports "my tree is empty
after I restarted the app", the first suspect is that the role, name,
or index of the object changed. Useful debugging steps:

1. Log `get_object_id` for the navigator before and after.
2. If only one field differs, consider whether it should be excluded
   from the tuple in `identity.py`.
3. For UIA-rich apps, prefer `AutomationId` over `name` when
   available — already included in the tuple.

## Adding a feature

The usual shape is:

1. Extend the pure-Python core (new function in `tree.py`,
   `inheritance.py`, etc.) plus unit tests in `tests/`.
2. Expose it through `SemanticNavigator` if it is a navigation move,
   or directly in `plugin.py` if it is a one-shot operation.
3. If the user needs a UI, add a new file under `ui/` that follows the
   pattern of the existing dialogs.
4. Add a `@script`-decorated method on `GlobalPlugin`.
5. Update the README's shortcut table and this guide.

## Running and packaging

* Tests: `python tests/run.py`. No external dependencies. Install
  `pytest` if you want nicer output.
* Build: `scons` at the repo root. Produces
  `semanticTree-0.1.0.nvda-addon`.
* Install into NVDA: NVDA menu → Tools → Manage add-ons → Install.

For iterative development, symlink
`addon/globalPlugins/semanticTree` into
`%APPDATA%/nvda/addons/semanticTree/globalPlugins/` and restart NVDA
(`NVDA+Q`, then launch NVDA again) to pick up changes.

## Non-goals

* **Editing the real accessibility tree.** We never call UIA / IA2
  mutation APIs. The semantic tree is a *view* only.
* **Cross-user sharing.** State is local JSON. Exchange is manual.
* **Auto-inferring a "better" tree.** The point is that the user
  decides. Heuristic rearrangers belong on top of this add-on, not
  inside it.
