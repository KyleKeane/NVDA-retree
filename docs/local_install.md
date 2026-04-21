# Installing NVDA-retree on your own machine

Two ways in: **developer scratchpad** (fast, lets you reload after
each edit) and **packaged add-on** (what end users will use). Pick
the scratchpad for active development; pick the packaged install
once you're ready to smoke-test like a user.

Everything here is Windows-only because NVDA is Windows-only.

---

## Prerequisites

1. **NVDA 2022.1 or newer.** Older builds don't have the Developer
   Scratchpad feature and will refuse to load the add-on (our
   `manifest.ini` declares `minimumNVDAVersion = 2022.1`).
2. **Python 3.10+** — only needed if you want to build a `.nvda-addon`
   yourself or run the tests. You do **not** need Python on the path
   to use the scratchpad method, and NVDA ships with its own bundled
   Python internally.
3. **Git** — to clone the repo.

---

## Method A — Developer Scratchpad (recommended for development)

The scratchpad is a folder inside your NVDA config directory whose
contents NVDA loads at startup as if they were an installed add-on.
You drop your source straight in (or symlink it) and reload from
inside NVDA whenever you change a file. No build step, no install,
no restart for most edits.

### Step 1. Clone the repo

Open a command prompt or PowerShell window. You do not need admin
rights for any of this.

```powershell
cd %USERPROFILE%\Documents
git clone https://github.com/kylekeane/nvda-retree.git
cd nvda-retree
git checkout claude/nvda-semantic-tree-iLPd1
```

Replace the `cd %USERPROFILE%\Documents` with wherever you keep
source checkouts. Anywhere your user account can write will do.

### Step 2. Find your NVDA config directory

For an installed copy of NVDA this is almost always:

```
%APPDATA%\nvda
```

which is typically `C:\Users\<your-name>\AppData\Roaming\nvda`.

If you run NVDA as a **portable** copy, the config directory is the
`userConfig` folder next to `nvda.exe`. To confirm, open NVDA menu
&rarr; **Tools** &rarr; **View log** and look near the top for a
line like:

```
INFO - core.main (HH:MM:SS.sss):
Config dir: C:\Users\...\nvda
```

For the rest of this guide we'll call that directory `%NVDA_CONFIG%`.
In a normal command prompt you can literally use `%APPDATA%\nvda`.

### Step 3. Turn on the Developer Scratchpad

NVDA hides this behind the Advanced settings page on purpose — it
lets arbitrary Python code run inside NVDA, so enable it deliberately.

1. Press **NVDA+N** to open the NVDA menu.
2. Choose **Preferences** &rarr; **Settings...** (or press **NVDA+Ctrl+G**).
3. In the category list on the left, select **Advanced**.
4. Tick **"I understand that changing these advanced settings may
   cause NVDA to function incorrectly"**.
5. Tick **"Enable loading custom code from Developer Scratchpad
   directory"**.
6. Click **OK**.

You have just created (if it didn't already exist) the folder
`%NVDA_CONFIG%\scratchpad\` with a few subfolders inside
(`globalPlugins`, `appModules`, `synthDrivers`, etc.).

### Step 4. Put our plugin inside the scratchpad

Our code lives under `addon/globalPlugins/semanticTree/` in the
repo. NVDA expects it under `scratchpad/globalPlugins/semanticTree/`
in the config directory. There are two ways to get it there — a
directory junction (recommended, survives future `git pull`s) or a
plain copy.

#### Option 4a: Directory junction (recommended)

A junction is a Windows filesystem pointer. Any time NVDA reads from
the junction it transparently reads from your checkout, so
`git pull` followed by a plugin reload is all it takes to pick up
new commits. Junctions do **not** need admin rights.

Open a **Command Prompt** (not PowerShell — the `/J` flag is a
`cmd.exe` built-in). Then:

```cmd
mklink /J "%APPDATA%\nvda\scratchpad\globalPlugins\semanticTree" "%USERPROFILE%\Documents\nvda-retree\addon\globalPlugins\semanticTree"
```

Adjust the second path if you cloned somewhere other than
`%USERPROFILE%\Documents\nvda-retree`. If the command succeeds it
prints `Junction created for ...`.

To remove the junction later: `rmdir "%APPDATA%\nvda\scratchpad\globalPlugins\semanticTree"`
(this removes the junction only — the real files in your checkout
are untouched).

#### Option 4b: Plain copy

If you prefer to copy, using File Explorer or `xcopy`:

```cmd
xcopy /E /I "%USERPROFILE%\Documents\nvda-retree\addon\globalPlugins\semanticTree" "%APPDATA%\nvda\scratchpad\globalPlugins\semanticTree"
```

You will have to re-copy every time you change code.

### Step 5. Reload plugins inside NVDA

Press **NVDA+Ctrl+F3**. NVDA will say "Plugins reloaded." Our code
is now live. From this point, the seven gestures (see table below)
are available.

> **When reload is not enough.** `NVDA+Ctrl+F3` re-runs every
> plugin's module code. It does **not** re-read the gesture map or
> the script category. If you add or rename a gesture, or change
> `scriptCategory`, you need a full restart (**NVDA+Q** &rarr;
> Restart, or **NVDA+Ctrl+Q** on some builds).

### Step 6. Verify it loaded

Open **NVDA menu &rarr; Tools &rarr; View log** and look near the
bottom. If the plugin loaded cleanly you'll see no red errors
referring to `semanticTree`. If it failed to import, the traceback
will name the failing module and line number — the log is the first
place to look when something goes wrong.

You can also confirm the gestures are registered: **NVDA menu
&rarr; Preferences &rarr; Input gestures...** and type "semantic" in
the filter — you should see a **Semantic Tree** category with seven
entries.

### Step 7. The development loop

Once the junction is in place, the typical cycle is:

1. Edit a file in your checkout.
2. Press **NVDA+Ctrl+F3** to reload plugins.
3. Try the gesture.
4. If something went wrong, **Tools &rarr; View log** tells you why.

`git pull` on the checkout picks up new code; a reload makes it
live. No rebuild, no reinstall.

---

## Method B — Build a packaged `.nvda-addon` and install it

Use this once you want to smoke-test exactly what a user would install,
or when you want to share a build with someone who doesn't have the
checkout. This is also how the add-on would eventually ship.

### Shortcut: grab the pre-built `.nvda-addon` from GitHub

You don't *have* to build locally. Every merge to `main` automatically
publishes a fresh `.nvda-addon` at:

<https://github.com/KyleKeane/NVDA-retree/releases/tag/main-latest>

Download the attached `semanticTree-X.Y.Z.nvda-addon` and jump to
Step 2 below. That tag is force-moved on every push to `main`, so
the download URL stays stable and the file there always matches
the current `main`. Marked as a pre-release so NVDA's in-add-on
update check ignores it (it only offers stable `vX.Y.Z`).

If you want a specific commit or unmerged PR, build locally:

### Step 1. Clone and build

```powershell
cd %USERPROFILE%\Documents
git clone https://github.com/kylekeane/nvda-retree.git
cd nvda-retree
git checkout claude/nvda-semantic-tree-iLPd1
py -3 tools\build_addon.py
```

(`py -3` is the Windows Python launcher. If you installed Python
differently, `python` may work too.)

You should see:

```
built .../semanticTree-0.1.0.nvda-addon (19.8 KB)
```

in the repo root.

### Step 2. Install the add-on from NVDA

1. Press **NVDA+N** &rarr; **Tools** &rarr; **Add-on store...**
   (on NVDA 2023.2+) or **Manage add-ons...** (older builds).
2. Click **Install from external source** (or **Install...**).
3. Navigate to the `.nvda-addon` file you just built and open it.
4. NVDA shows a confirmation dialog listing the add-on's name,
   version, and author. Accept.
5. When prompted, click **Restart NVDA now**.

After NVDA restarts the add-on is live and all seven gestures are
registered.

### Step 3. Uninstall / upgrade

Open the Add-on store / Manage add-ons window again, select
**Semantic Tree**, and click **Remove** (or **Disable** if you just
want to pause it without losing your state file). NVDA will ask to
restart. Your `semanticTree.json` config file stays behind in
`%APPDATA%\nvda\` unless you delete it manually; that means
reinstalling brings back every label and assignment.

Uninstalling is not required to install a new build on top of the
old one — when you open a newer `.nvda-addon` with the same name,
NVDA will offer to upgrade.

---

## Gestures (reference)

| Shortcut | Action |
|---|---|
| **NVDA+Ctrl+Shift+Up** | Move to the semantic parent |
| **NVDA+Ctrl+Shift+Down** | Move to the first semantic child |
| **NVDA+Ctrl+Shift+Left** | Previous semantic sibling |
| **NVDA+Ctrl+Shift+Right** | Next semantic sibling |
| **NVDA+Ctrl+Shift+L** | Label / re-label the current object |
| **NVDA+Ctrl+Shift+A** | Assign the current object under a semantic parent |
| **NVDA+Ctrl+Shift+F** | Search the semantic tree |

All rebindable from **Preferences &rarr; Input gestures &rarr; Semantic Tree**.

---

## Troubleshooting

### Nothing happens when I press a gesture

- Open **Tools &rarr; View log**. If the plugin failed to import,
  the traceback is there.
- Check **Preferences &rarr; Input gestures...**, filter by
  "semantic". If the entries are missing, NVDA didn't load the
  plugin at all — usually a path typo in the junction.
- Confirm the junction points where you think it does:
  `dir "%APPDATA%\nvda\scratchpad\globalPlugins\semanticTree"`
  should list `plugin.py`, `navigator.py`, etc.

### "No navigator object" every time

The NVDA navigator object hasn't been set yet. Press **NVDA+Numpad5**
(desktop layout) or **NVDA+Shift+O** (laptop) first to move it to
the focused control.

### I edited a file but nothing changed

You forgot **NVDA+Ctrl+F3**. Or: you changed a gesture binding /
script category / class-level attribute, which requires a full
NVDA restart (**NVDA+Q** &rarr; Restart).

### The state file got corrupted

If `%APPDATA%\nvda\semanticTree.json` ever becomes unparseable, the
add-on moves it aside as `semanticTree.json.corrupt-<timestamp>`
and starts fresh. You can inspect the backup to recover what was
there. The add-on will log a warning to NVDA's log when this
happens.

### Where is my data?

`%APPDATA%\nvda\semanticTree.json` — labels and assignments.
Nothing else is persisted.

---

## Running the tests (optional, development)

If you want to confirm a checkout is healthy before loading it into
NVDA:

```powershell
cd %USERPROFILE%\Documents\nvda-retree
py -3 tests\run.py
```

All tests run with only Python's standard library. You should see
`all 52 green` (or whatever the current count is) at the end.
