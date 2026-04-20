# Smoke test — NVDA-retree

This is a structured test for a human operator running the add-on
inside NVDA for the first time. Nothing here requires any knowledge
of the source code. You just need to follow the steps, listen to
what NVDA says, and fill in the short report at the bottom.

Expected time: **15–20 minutes**.

---

## What this add-on does (60-second overview)

Inside NVDA, every app has an "accessibility tree" — a hierarchy of
objects (buttons, text fields, menus, etc.) that NVDA can read and
navigate. **NVDA-retree** lets a user re-arrange that tree into a
personal layout. You can:

- Attach a custom **label** to a poorly-named object.
- **Assign** any object under any other object, creating a
  semantic hierarchy of your own.
- **Navigate** through that semantic hierarchy with the arrow keys
  (NVDA's own navigator object follows along so everything else
  keeps working normally).
- **Search** everything you have placed in the tree by label,
  role, app, or path.

---

## 0. What you need

- A Windows 10 or 11 machine.
- NVDA **2022.1 or newer** installed. Free download:
  https://www.nvaccess.org/download/ . Accept defaults during
  install.
- The add-on file: `semanticTree-0.1.0.nvda-addon`. Ask the
  developer where it is — it will either be attached to the task or
  downloadable from a GitHub Actions run artifact on the project
  repo.
- A modern web browser installed (Edge, Firefox, or Chrome — any
  of the three).

### NVDA essentials (if you have never used NVDA before)

- NVDA is a screen reader. Everything you do shows up as speech.
- The **NVDA key** by default is either **Insert** or **CapsLock**.
  If you have a numpad, the default is Insert. References like
  **NVDA+L** mean "hold NVDA, press L, release both". Give NVDA ~1
  second to react — it is busy talking.
- To **pause speech** briefly, press **Ctrl**. To **stop** the
  current utterance, press **NVDA+S** once (speech mode cycles —
  keep at default "talk").
- To **quit NVDA**: press **NVDA+Q**, Enter, or use the system tray.

---

## 1. Install the add-on

1. Start NVDA. You will hear "NVDA started".
2. Press **NVDA+N** to open the NVDA menu. Arrow-down to
   **Tools**, press Enter, then arrow-down to **Add-on store…** and
   press Enter.
   - On older NVDA it may be called **Manage add-ons…** — the path
     is the same.
3. In the Add-on store, press **Tab** until you reach **Install
   from external source** (or **Install…** on older builds) and
   press Enter.
4. A standard file-picker dialog opens. Navigate to where
   `semanticTree-0.1.0.nvda-addon` was saved, select it, press Enter.
5. NVDA shows a confirmation dialog listing the add-on's name,
   version, and author. Press the **Yes** button.
6. When prompted to restart, press **Restart NVDA now**.

**Pass:** NVDA restarts and comes back up. No red error dialogs.

**Fail:** Any "Error installing" dialog, or NVDA refuses to start
after restart. Write down the text of any error dialog in the
report at the bottom.

---

## 2. Confirm the gestures are registered

1. Press **NVDA+N** &rarr; **Preferences** &rarr; **Input gestures…**.
2. In the **Filter by** box, type `semantic`.
3. The tree below should contain a category called **Semantic Tree**
   with **seven** entries:
   - Move to the semantic parent of the current navigator object
   - Move to the first semantic child of the current navigator object
   - Move to the previous semantic sibling
   - Move to the next semantic sibling
   - Set a custom label for the current navigator object
   - Assign the current navigator object to a position in the semantic tree
   - Search the semantic tree by label, role, or path

**Pass:** Seven entries are visible under Semantic Tree.

**Fail:** Fewer than seven entries, or no Semantic Tree category
at all.

Close the dialog with Escape when done.

---

## 3. Open the add-on help

1. Press **NVDA+N** &rarr; **Tools** &rarr; **Add-on store…**.
2. Arrow through the installed add-ons until you hear **Semantic
   Tree**.
3. Press **Tab** to reach the action buttons and find **Help** (or
   **Documentation**). Press Enter or Space.

**What is expected to happen:** the system opens the help file. On
this version the file is named `readme.md`. Windows has no default
app for `.md` files, so **on first click Windows will show a "How
do you want to open this file?" prompt**. Pick **Notepad** (or any
text editor you prefer). Tick "always use this app" if you want
the prompt to stop appearing. From then on, clicking Help opens
the file in your chosen editor.

**Pass:** The help file opens in Notepad (or the app you picked)
and shows plain text describing the shortcuts and the search syntax.

**Fail:** Clicking Help produces an error dialog, or Windows
reports the file does not exist.

---

## 4. Position NVDA's navigator on something testable

For the remaining tests we need NVDA's "navigator object" placed on
a specific control. The simplest target is **Notepad** because its
accessibility tree is small and predictable.

1. Open **Notepad** (Windows key, type `notepad`, Enter).
2. Type `Hello world` so the window is not blank.
3. Press **NVDA+Numpad5** (desktop layout) **or NVDA+Shift+O**
   (laptop layout). This commands NVDA's navigator to "report the
   current object" — which also anchors it there. NVDA should
   announce the Notepad editor control.

**Pass:** NVDA says something like "edit" or "document Hello
world".

If that does not work, try **NVDA+Numpad8** then **NVDA+Numpad2**
to move the navigator around and hear where it is.

---

## 5. Test: Label a poorly-named object

1. With the navigator still on the Notepad edit area, press
   **NVDA + Ctrl + Shift + L**.
2. A small dialog appears titled **Semantic Tree: label** with an
   empty text box. Your caret should already be in the text box.
3. Type `My Notepad`. Press Enter.

**Pass:** NVDA announces **Label saved**.

4. Press **NVDA+Numpad5** again to report the current object.

**Pass:** NVDA now announces **My Notepad** (instead of "edit" or
whatever it said in section 4).

**Fail:** NVDA is silent after step 3, reports an error, or does
not substitute the label in step 4. Note exactly what you hear.

---

## 6. Test: Assign a semantic parent

1. Press **NVDA + Ctrl + Shift + A**.
2. A dialog appears titled **Semantic Tree: assign** with a tree
   view. On a fresh install the only entry is **(top level)**.
3. The tree item should already be selected. Press **Enter**.

**Pass:** NVDA announces **Assigned**.

4. Repeat the test: press **NVDA + Ctrl + Shift + A** again on the
   same object. The dialog opens. Press **Escape** to cancel.

**Pass:** The dialog closes silently; no error is announced.

---

## 7. Test: Semantic navigation (four arrow keys)

Stay on the Notepad edit area you just labelled.

1. Press **NVDA + Ctrl + Shift + Up**.
   - Expected: NVDA announces **No semantic parent** (because the
     Notepad edit is a root of your semantic tree — you assigned
     it to "(top level)" a moment ago).
2. Press **NVDA + Ctrl + Shift + Down**.
   - Expected: NVDA announces something describing the first child
     (or **No semantic children** if nothing else is assigned yet).
3. Press **NVDA + Ctrl + Shift + Left**.
   - Expected: NVDA announces **No previous semantic sibling** (or
     jumps to one).
4. Press **NVDA + Ctrl + Shift + Right**.
   - Expected: NVDA announces **No next semantic sibling** (or
     jumps to one).

**Pass:** Each of the four keys either announces a meaningful
"No …" message OR moves to another object. Nothing crashes, no
red traceback appears in NVDA's log.

**Fail:** Silence (gesture had no effect) or a Python traceback.
Get the traceback text — see section 11 below for how.

---

## 8. Test: Search

1. Press **NVDA + Ctrl + Shift + F**.
2. A dialog appears titled **Semantic Tree: search** with a text
   box at the top and a list below. The list should already contain
   at least one entry: **My Notepad**.
3. In the search box, type `note`. The list should narrow in real
   time.
4. Press **Tab** to move into the list (or **Down** arrow). Arrow
   to **My Notepad**. Press **Enter**.

**Pass:** The dialog closes and NVDA announces **My Notepad**
again (the navigator has jumped back to that object).

**Fail:** The list is empty after step 2, or pressing Enter does
nothing, or NVDA announces "Could not locate that object on screen
any more" (this would mean the live object has been lost — not
expected for a current Notepad).

---

## 9. Test: Persistence across a restart

1. Close Notepad.
2. Press **NVDA+Q**, Enter to quit NVDA entirely.
3. Start NVDA again.
4. Reopen Notepad, type some text, press **NVDA+Numpad5** to land
   on the edit area.

**Pass:** NVDA still announces **My Notepad** (your label survived
the restart).

**Fail:** NVDA announces "edit" or similar — the label was lost.

---

## 10. Test: Corrupt-state recovery

This confirms the add-on does not wedge NVDA if its saved state
gets scrambled.

1. Quit NVDA (**NVDA+Q**, Enter).
2. Open **File Explorer**, paste `%APPDATA%\nvda` into the address
   bar, Enter. You should be in NVDA's user config folder.
3. Find the file **semanticTree.json**. Open it with Notepad.
4. **Replace its entire contents with the word** `garbage` (no
   quotes) and save.
5. Start NVDA.

**Pass:** NVDA starts normally, no error dialog about the add-on.
Re-check the folder — you should now see a second file named
**semanticTree.json.corrupt-<some number>** (the add-on moved the
scrambled file aside). The live `semanticTree.json` is either
empty-shaped or recreated on first save.

**Fail:** NVDA shows a Python error dialog on startup, or cannot
start at all.

---

## 11. If anything fails: how to capture the detail we need

1. Inside NVDA press **NVDA+N** &rarr; **Tools** &rarr; **View log**.
2. The log window opens. Press **Ctrl+End** to jump to the bottom.
3. Scroll up and look for lines that contain `semanticTree`,
   `ERROR`, `Traceback`, or the text of the gesture you were
   testing.
4. Select the relevant block (a traceback is usually 5–20 lines).
   Copy it with **Ctrl+C**.
5. Paste the text into your bug report under **Logs** below.

If you cannot get the log out, a plain-English description is
still useful ("I pressed X, NVDA said Y").

---

## Report template

Please copy the block below into your reply and fill it in. Leave
any row as-is if that test passed with no notes.

```
Environment
  Windows version:
  NVDA version:
  Browser (if you opened Help):

Section 1 Install          : PASS / FAIL — notes:
Section 2 Gestures listed  : PASS / FAIL — notes:
Section 3 Help opens       : PASS / FAIL — notes:
Section 4 Navigator placed : PASS / FAIL — notes:
Section 5 Label            : PASS / FAIL — notes:
Section 6 Assign           : PASS / FAIL — notes:
Section 7 Four arrow moves : PASS / FAIL — notes:
Section 8 Search           : PASS / FAIL — notes:
Section 9 Persistence      : PASS / FAIL — notes:
Section 10 Corrupt recovery: PASS / FAIL — notes:

Anything that crashed, hung, or felt wrong:

Any NVDA log tracebacks (paste here):
```

That's it — thank you for running through this. Every "FAIL" with
a description saves a lot of guesswork back here.
