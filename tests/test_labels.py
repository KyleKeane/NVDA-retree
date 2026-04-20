from semanticTree.labels import LabelStore


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
