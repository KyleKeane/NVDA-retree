# NVDA-retree — Semantic Tree for NVDA

NVDA-retree is an NVDA add-on that lets you **re-arrange the accessibility
tree into your own mental model** without changing the application you are
reading. You pick objects you care about — a toolbar here, a button there,
an obscure landmark on a web page — and slot them under whatever parents
*make sense to you*. NVDA's normal object navigation keeps working
unchanged on the original tree; the semantic tree sits beside it as a
navigation aid, a labelling layer, and a searchable catalogue.

The add-on is named after its core trick: **re-tree**ing the accessibility
graph without touching the application.

---

## Status

**Foundation release (0.1.0).** Everything the user-facing feature list
below describes is wired up: four-way semantic navigation, custom labels,
parent assignment, live search. The underlying data model, persistence,
and inheritance logic are covered by unit tests. Expect rough edges in
the UI polish, translation coverage, and corner-case object identity —
see `docs/developer_guide.md` for where to help.

## What it does

### 1. A second tree, layered on the first

NVDA's built-in object navigation walks the accessibility tree that
Windows (UIA / IAccessible / IA2) exposes for a running application.
That tree is often noisy: deep nesting, redundant wrappers, and named
objects that do not match how you think about the UI.

NVDA-retree adds a *semantic tree* on top. You move navigator objects
under new parents; NVDA's own navigator moves invisibly in lock-step so
every other NVDA command (report focus, read current object, object
navigation helpers, etc.) keeps working against the real accessibility
tree.

### 2. Inheritance for everything you have not touched

You only ever record **one** piece of data: *this object's semantic
parent is that object*. Everything else is derived. When you move a
parent, the whole subtree under it follows automatically — because any
descendant you have not explicitly placed just inherits its nearest
explicitly-placed ancestor. Move one of those descendants, and its own
children follow it. The rule is a single sentence, which keeps the
whole system predictable.

### 3. Better labels

Some objects arrive with unhelpful names (`""`, `"Button 17"`, a raw
resource ID). A keystroke lets you attach a human-readable label. The
label is stored against a stable identity for that object and is used
by every surface of the add-on (navigation announcements, the assign
dialog, the search dialog).

### 4. An assignment dialog you can actually use

Picking a semantic parent blind is painful. When you press the assign
shortcut, NVDA-retree opens a tree view of the semantic tree as it
currently exists. Arrow-key around, pick a parent, press Enter. You
can also pick "(top level)" to make the current object a new root.

### 5. An item chooser, VoiceOver-style

A single shortcut opens a search dialog listing every object that has
ever been placed in the semantic tree. The filter understands plain
words (space-separated terms all have to match) and facet restrictions
(`role:button`, `app:firefox`, `-notepad` to exclude, etc.). Picking a
result moves the NVDA navigator straight to that object.

## Keyboard shortcuts

All gestures use **NVDA + Control + Shift** as a modifier prefix so they
never collide with NVDA's own navigation bindings.

| Gesture                               | Action                                            |
|---------------------------------------|---------------------------------------------------|
| NVDA + Ctrl + Shift + Up              | Move to semantic parent                           |
| NVDA + Ctrl + Shift + Down            | Move to first semantic child                      |
| NVDA + Ctrl + Shift + Left            | Move to previous semantic sibling                 |
| NVDA + Ctrl + Shift + Right           | Move to next semantic sibling                     |
| NVDA + Ctrl + Shift + L               | Set / clear custom label for current object       |
| NVDA + Ctrl + Shift + A               | Assign current object under a semantic parent     |
| NVDA + Ctrl + Shift + F               | Search / jump to a semantic object                |

All gestures are re-bindable from **NVDA menu → Preferences → Input
gestures → Semantic Tree**.

## How the pieces fit together

```
accessibility tree          semantic tree
(given by Windows)          (built by the user)

      Window                      Window
        ├─ Toolbar                  ├─ Reload      ← moved by user
        │   ├─ Reload               └─ Navigation  ← new grouping label
        │   ├─ Back                     ├─ Back
        │   └─ Home                     └─ Home
        └─ Main pane            (everything else inherits
            └─ Link              its usual parent, untouched)
```

The semantic tree is *not* a copy. It stores only the arrows the user
has drawn. Everything else is answered at lookup time by walking the
real accessibility tree and consulting those arrows.

## Installation

**Full step-by-step instructions are in
[`docs/local_install.md`](docs/local_install.md).** Short version:

### For day-to-day development (recommended while the project is pre-1.0)

Use NVDA's **Developer Scratchpad**. Enable it under NVDA &rarr;
Preferences &rarr; Settings &rarr; Advanced, then point a directory
junction at your checkout:

```cmd
mklink /J "%APPDATA%\nvda\scratchpad\globalPlugins\semanticTree" "<path-to-your-clone>\addon\globalPlugins\semanticTree"
```

Press **NVDA+Ctrl+F3** to (re)load plugins. No build, no restart
needed for most edits.

### To test the packaged experience

```powershell
py -3 tools\build_addon.py
```

Then in NVDA: **Tools &rarr; Add-on store &rarr; Install from
external source** and point it at `semanticTree-0.1.0.nvda-addon`.
Restart when prompted.

Either path produces the same running add-on; the scratchpad just
lets you reload after edits without rebuilding.

## Staying up to date

Once installed, the add-on can update itself from GitHub:
**NVDA → Tools → Check for Semantic Tree updates…**. The menu item
hits `api.github.com/repos/KyleKeane/NVDA-retree/releases/latest`,
shows the release notes, and downloads the `.nvda-addon` straight
into NVDA's standard installer. No background network traffic —
updates only run when you click the menu item.

Your labels and assignments in `%APPDATA%\nvda\semanticTree.json`
are never touched by an update. See `addon/doc/en/readme.md` for
the user-side walkthrough, and [`CONTRIBUTING.md`](CONTRIBUTING.md#releasing)
for how to cut a release that propagates to existing installs.

## Running the tests

```
python tests/run.py
```

The pure-Python core (tree, inheritance, labels, storage, search) runs
without NVDA and is fully covered.

## License

MIT. See `LICENSE`.
