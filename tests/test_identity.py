"""Tests for the persistent, path-based identity scheme.

The identity is ``(app_name, path)`` where ``path`` is a tuple of
``(role, discriminator, sibling_index)`` node signatures walking from
the root ancestor down to the object. These tests cover the
correctness properties we care about most: cross-session stability,
path disambiguation, robustness against dynamic window titles, and
resilience to auto-generated automation IDs.
"""

from semanticTree.identity import get_object_id

from fakes import FakeObject


# ---------- basic shape and degenerate cases ----------


def test_none_returns_none():
	assert get_object_id(None) is None


def test_id_is_hashable():
	obj = FakeObject("X", role="button")
	assert hash(get_object_id(obj)) is not None


def test_id_is_tuple_of_app_and_path():
	obj = FakeObject("X", role="button", app_name="myapp")
	oid = get_object_id(obj)
	assert isinstance(oid, tuple)
	assert oid[0] == "myapp"
	assert isinstance(oid[1], tuple)  # path


def test_missing_appmodule_falls_back_cleanly():
	"""Objects that don't have an appModule (unusual but possible)
	still produce a non-empty tuple, with an empty app field."""
	obj = FakeObject("X", role="button")
	del obj.appModule
	oid = get_object_id(obj)
	assert oid[0] == ""
	assert isinstance(oid[1], tuple)


# ---------- core property: cross-session stability ----------


def _build_notepad_tree(app_name: str = "notepad"):
	"""Build a minimal Notepad-shaped tree. Returns the edit control."""
	window = FakeObject(
		name="Untitled - Notepad",
		role="window",
		app_name=app_name,
		window_class_name="Notepad",
	)
	edit = window.add(FakeObject(
		name="",
		role="edit",
		app_name=app_name,
		window_class_name="Edit",
	))
	return edit


def test_same_tree_rebuilt_yields_equal_ids():
	"""Restart stability: we rebuild the same logical tree from
	scratch. Identity must match because nothing in it depends on
	OS-assigned handles."""
	edit_today = _build_notepad_tree()
	edit_tomorrow = _build_notepad_tree()
	assert get_object_id(edit_today) == get_object_id(edit_tomorrow)


# ---------- path disambiguates ----------


def test_same_name_in_different_subtrees_gets_different_ids():
	"""Two buttons named "OK" in sibling panels must be distinguishable
	because the path walks differ."""
	window = FakeObject("App", role="window", window_class_name="App")
	left = window.add(FakeObject("Left", role="pane"))
	right = window.add(FakeObject("Right", role="pane"))
	left_ok = left.add(FakeObject("OK", role="button"))
	right_ok = right.add(FakeObject("OK", role="button"))
	assert get_object_id(left_ok) != get_object_id(right_ok)


def test_sibling_index_disambiguates_duplicate_signatures():
	"""Three identical listitems under the same parent get distinct
	``sibling_index`` values 0, 1, 2."""
	window = FakeObject("App", role="window", window_class_name="App")
	listbox = window.add(FakeObject("Results", role="list"))
	items = [listbox.add(FakeObject("", role="listItem")) for _ in range(3)]
	ids = [get_object_id(i) for i in items]
	assert len({ids[0], ids[1], ids[2]}) == 3
	# Final tuple element of the LAST node on each path is the sibling index.
	assert ids[0][1][-1][2] == 0
	assert ids[1][1][-1][2] == 1
	assert ids[2][1][-1][2] == 2


# ---------- dynamic window title does not bleed ----------


def test_dynamic_top_level_name_does_not_change_descendant_ids():
	"""A Notepad window whose title is 'Document1 - Notepad' and one
	whose title is 'Document2 - Notepad' should produce the same IDs
	for their edit children, because the top-level uses
	windowClassName (stable) instead of name (dynamic)."""
	win1 = FakeObject(
		name="Document1 - Notepad", role="window",
		app_name="notepad", window_class_name="Notepad",
	)
	win2 = FakeObject(
		name="Document2 - Notepad", role="window",
		app_name="notepad", window_class_name="Notepad",
	)
	edit1 = win1.add(FakeObject("", role="edit", window_class_name="Edit"))
	edit2 = win2.add(FakeObject("", role="edit", window_class_name="Edit"))
	assert get_object_id(edit1) == get_object_id(edit2)


# ---------- automation ID stability heuristic ----------


def test_stable_automation_id_is_used_as_discriminator():
	obj = FakeObject("Anything", role="button", automation_id="reload-button")
	oid = get_object_id(obj)
	# Last node's discriminator slot.
	assert oid[1][-1][1] == "reload-button"


def test_guid_shaped_automation_id_is_ignored():
	"""WPF / Electron emit IDs that change per launch. They must fall
	back to ``name``."""
	guid_id = "550e8400-e29b-41d4-a716-446655440000"
	a = FakeObject("SaveButton", role="button", automation_id=guid_id)
	b = FakeObject("SaveButton", role="button", automation_id="")
	# With the GUID ignored, both fall back to name. IDs match.
	assert get_object_id(a) == get_object_id(b)


def test_numeric_only_automation_id_is_ignored():
	"""All-digit IDs look like auto-generated indices and are unsafe."""
	a = FakeObject("Save", role="button", automation_id="12345")
	b = FakeObject("Save", role="button", automation_id="")
	assert get_object_id(a) == get_object_id(b)


def test_window_class_name_is_used_when_no_stable_automation_id():
	obj = FakeObject("", role="edit", window_class_name="Edit")
	oid = get_object_id(obj)
	assert oid[1][-1][1] == "Edit"


# ---------- different apps remain distinct ----------


def test_different_apps_produce_different_ids_even_with_same_structure():
	a = FakeObject("Main", role="window", app_name="firefox", window_class_name="MozillaWindowClass")
	b = FakeObject("Main", role="window", app_name="chrome", window_class_name="Chrome_WidgetWin_1")
	assert get_object_id(a) != get_object_id(b)
	assert get_object_id(a)[0] == "firefox"
	assert get_object_id(b)[0] == "chrome"
