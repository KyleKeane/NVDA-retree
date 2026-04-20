from semanticTree.identity import get_object_id

from fakes import FakeObject


def test_none_returns_none():
	assert get_object_id(None) is None


def test_deterministic_for_same_attributes():
	a = FakeObject("Reload", "button", app_name="firefox", automation_id="reload-btn")
	b = FakeObject("Reload", "button", app_name="firefox", automation_id="reload-btn")
	# Give them the same window handle so they're the "same object" identity-wise.
	b.windowHandle = a.windowHandle
	assert get_object_id(a) == get_object_id(b)


def test_different_app_differs():
	a = FakeObject("Reload", "button", app_name="firefox")
	b = FakeObject("Reload", "button", app_name="chrome")
	b.windowHandle = a.windowHandle
	assert get_object_id(a) != get_object_id(b)


def test_missing_appModule_falls_back_cleanly():
	"""Objects that don't have an appModule (unusual but possible) should
	still produce a non-empty tuple — just with an empty app field."""
	obj = FakeObject("X")
	del obj.appModule
	oid = get_object_id(obj)
	assert isinstance(oid, tuple)
	assert oid[0] == ""


def test_id_is_hashable():
	obj = FakeObject("X")
	assert hash(get_object_id(obj)) is not None


def test_missing_automation_id_tolerated():
	obj = FakeObject("X", automation_id="")
	oid = get_object_id(obj)
	assert oid[5] == ""


def test_pulls_automation_id_when_present():
	obj = FakeObject("X", automation_id="pay-button")
	assert get_object_id(obj)[5] == "pay-button"


def test_first_child_index_preserved():
	"""Regression: int(0 or -1) collapsed the first-child index to -1,
	colliding with the missing-attribute sentinel. Every first child
	looked identical to every other first child."""
	parent = FakeObject("P")
	first = parent.add(FakeObject("A"))
	second = parent.add(FakeObject("B"))
	assert first.indexInParent == 0
	assert second.indexInParent == 1
	assert get_object_id(first)[6] == 0
	assert get_object_id(second)[6] == 1


def test_window_handle_zero_preserved():
	obj = FakeObject("X")
	obj.windowHandle = 0
	assert get_object_id(obj)[1] == 0


def test_missing_index_uses_sentinel():
	obj = FakeObject("X")
	del obj.indexInParent
	assert get_object_id(obj)[6] == -1
