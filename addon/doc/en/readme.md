# Semantic Tree

NVDA-retree lets you re-arrange NVDA's accessibility tree into your own
mental model without changing the application you are reading.

## Shortcuts

* **NVDA + Ctrl + Shift + Up / Down / Left / Right** — move through the
  semantic tree (parent / first child / previous sibling / next sibling).
* **NVDA + Ctrl + Shift + L** — set or clear a custom label for the
  current navigator object.
* **NVDA + Ctrl + Shift + A** — assign the current navigator object
  under a semantic parent (picked from a tree dialog).
* **NVDA + Ctrl + Shift + F** — search the semantic tree by label,
  role, app, or path.

All shortcuts can be re-bound from NVDA → Preferences → Input gestures
→ Semantic Tree.

## Search query syntax

Multiple terms are AND-ed. Terms can be scoped to a facet with
`facet:value`. A leading `-` negates.

* `reload` — matches any facet containing "reload".
* `role:button firefox` — buttons in Firefox.
* `reload -notepad` — "reload" but not in Notepad.

Facets available: `label`, `role`, `app`, `path`.

## Where does my data live?

Your labels and assignments are stored as JSON in
`%APPDATA%/nvda/semanticTree.json`. If that file ever becomes
unreadable, the add-on quarantines it as
`semanticTree.json.corrupt-<timestamp>` and starts fresh, so a bad
file cannot wedge NVDA.

## Reporting problems

See the [project page](https://github.com/kylekeane/nvda-retree).
