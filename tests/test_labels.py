from semanticTree.labels import LabelStore
from semanticTree.patterns import WILDCARD


def test_set_get_clear():
	store = LabelStore()
	store.set("id", "Hello")
	assert store.get("id") == "Hello"
	store.clear("id")
	assert store.get("id") is None


def test_empty_label_clears():
	store = LabelStore()
	store.set("id", "Hello")
	store.set("id", "")
	assert store.get("id") is None


def test_round_trip():
	store = LabelStore()
	store.set(("app", 1, "name"), "My button")
	restored = LabelStore.from_dict(store.to_dict())
	assert restored.get(("app", 1, "name")) == "My button"


def test_round_trip_with_nested_path_preserves_hashability():
	"""Regression: from_dict used to convert only the outer list to a
	tuple, leaving the nested path as an unhashable list. That broke
	every subsequent dict lookup and sent state files silently to
	quarantine on every NVDA restart."""
	exact = ("firefox", (("window", "MozillaWindowClass", 0), ("button", "Reload", 2)))
	store = LabelStore()
	store.set(exact, "Refresh page")
	restored = LabelStore.from_dict(store.to_dict())
	# Key must survive as hashable and look up cleanly.
	assert restored.get(exact) == "Refresh page"


# ---------- pattern fallback ----------


def _make_id(app, *nodes):
	return (app, tuple(nodes))


def test_pattern_label_matches_live_with_different_leaf_name():
	store = LabelStore()
	stored = _make_id("firefox",
		("window", "MozillaWindowClass", 0),
		("button", WILDCARD, 3),
	)
	store.set(stored, "Save button")
	live = _make_id("firefox",
		("window", "MozillaWindowClass", 0),
		("button", "Save As…", 3),
	)
	assert store.get(live) == "Save button"


def test_exact_match_beats_pattern():
	store = LabelStore()
	store.set(
		_make_id("firefox", ("button", WILDCARD, 0)),
		"generic",
	)
	store.set(
		_make_id("firefox", ("button", "Reload", 0)),
		"specific",
	)
	live = _make_id("firefox", ("button", "Reload", 0))
	assert store.get(live) == "specific"


def test_more_specific_pattern_wins_over_looser_one():
	store = LabelStore()
	store.set(
		_make_id("firefox", ("button", WILDCARD, WILDCARD)),
		"any button",
	)
	store.set(
		_make_id("firefox", ("button", WILDCARD, 3)),
		"fourth button",
	)
	# Both match; the one with the concrete sibling_index is more specific.
	live = _make_id("firefox", ("button", "Reload", 3))
	assert store.get(live) == "fourth button"


def test_pattern_does_not_match_across_apps():
	store = LabelStore()
	store.set(
		_make_id("firefox", ("button", WILDCARD, 0)),
		"Firefox button",
	)
	live = _make_id("chrome", ("button", "Reload", 0))
	assert store.get(live) is None
