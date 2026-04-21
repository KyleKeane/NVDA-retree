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

## Staying up to date

NVDA-retree can update itself from GitHub with one click.

* Press **NVDA+N** to open the NVDA menu.
* Choose **Tools → Check for Semantic Tree updates…**

A brief "Checking…" indicator appears, then one of three dialogs:

* **Up to date** — you are running the latest release.
* **Update available** — a new version has been published. The
  dialog shows the release notes; click **Install now** and NVDA
  downloads the add-on and hands it to its standard installer
  (you will see the usual confirmation dialog and a restart
  prompt).
* **Could not check** — GitHub was unreachable or the request
  failed. Check your internet connection and try again.

The check only runs when you click the menu item. There is no
background network activity.

## Where does my data live?

Your labels and assignments are stored as JSON in
`%APPDATA%/nvda/semanticTree.json`. This file lives **outside** the
add-on's own folder, so installing an update never touches it —
your labels and assignments survive every upgrade.

If that file ever becomes unreadable, the add-on renames it aside
as `semanticTree.json.corrupt-<timestamp>` and starts fresh, so a
bad file cannot wedge NVDA. The same mechanism handles one rare
case during upgrades: if a new version changes the internal
file format in a way that cannot be read back, the old file is
quarantined the same way. The release notes will call this out
explicitly when it applies.

## Reporting problems

See the [project page](https://github.com/kylekeane/nvda-retree).
