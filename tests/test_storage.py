import os

from semanticTree import storage
from semanticTree.labels import LabelStore
from semanticTree.tree import SemanticTree


def test_save_load_round_trip(tmp_path):
	path = os.path.join(str(tmp_path), "data.json")
	tree = SemanticTree()
	labels = LabelStore()
	tree.assign(("app", 1, "a"), None)
	tree.assign(("app", 1, "b"), ("app", 1, "a"))
	labels.set(("app", 1, "a"), "Top")
	storage.save(path, tree, labels)
	loaded_tree, loaded_labels = storage.load(path)
	assert loaded_tree.parent_of(("app", 1, "b")) == ("app", 1, "a")
	assert loaded_labels.get(("app", 1, "a")) == "Top"


def test_load_missing_returns_empty(tmp_path):
	tree, labels = storage.load(os.path.join(str(tmp_path), "nope.json"))
	assert list(tree.assigned_ids()) == []
	assert list(labels.items()) == []
