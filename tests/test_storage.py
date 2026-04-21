import glob
import os
import tempfile
from contextlib import contextmanager

from semanticTree import storage
from semanticTree.labels import LabelStore
from semanticTree.tree import SemanticTree


@contextmanager
def _tempdir():
	d = tempfile.mkdtemp(prefix="semtree_")
	try:
		yield d
	finally:
		import shutil
		shutil.rmtree(d, ignore_errors=True)


def test_save_load_round_trip():
	with _tempdir() as d:
		path = os.path.join(d, "data.json")
		tree = SemanticTree()
		labels = LabelStore()
		tree.assign(("app", 1, "a"), None)
		tree.assign(("app", 1, "b"), ("app", 1, "a"))
		labels.set(("app", 1, "a"), "Top")
		storage.save(path, tree, labels)
		loaded_tree, loaded_labels = storage.load(path)
		assert loaded_tree.parent_of(("app", 1, "b")) == ("app", 1, "a")
		assert loaded_labels.get(("app", 1, "a")) == "Top"


def test_load_missing_returns_empty():
	with _tempdir() as d:
		tree, labels = storage.load(os.path.join(d, "nope.json"))
		assert list(tree.assigned_ids()) == []
		assert list(labels.items()) == []


def test_corrupt_json_is_quarantined():
	with _tempdir() as d:
		path = os.path.join(d, "data.json")
		with open(path, "w", encoding="utf-8") as f:
			f.write("this is not JSON {[")
		tree, labels = storage.load(path)
		assert list(tree.assigned_ids()) == []
		assert list(labels.items()) == []
		assert not os.path.exists(path)
		assert glob.glob(os.path.join(d, "data.json.corrupt-*"))


def test_non_object_top_level_is_quarantined():
	with _tempdir() as d:
		path = os.path.join(d, "data.json")
		with open(path, "w", encoding="utf-8") as f:
			f.write('["not", "an", "object"]')
		tree, labels = storage.load(path)
		assert list(tree.assigned_ids()) == []
		assert glob.glob(os.path.join(d, "data.json.corrupt-*"))


def test_v1_file_is_quarantined():
	"""Version-1 state used unstable window-handle-based IDs. There is
	no safe automatic migration, so we quarantine and start fresh."""
	import json
	with _tempdir() as d:
		path = os.path.join(d, "data.json")
		with open(path, "w", encoding="utf-8") as f:
			json.dump({
				"version": 1,
				"tree": {"assignments": [[["app", 123, 0, "button", "Reload", "", 2], None]]},
				"labels": {"labels": [[["app", 123, 0, "button", "Reload", "", 2], "My reload"]]},
			}, f)
		tree, labels = storage.load(path)
		assert list(tree.assigned_ids()) == []
		assert list(labels.items()) == []
		assert not os.path.exists(path)
		assert glob.glob(os.path.join(d, "data.json.corrupt-*"))


def test_unknown_future_version_is_quarantined():
	"""Defence in depth: if someone rolls back from a newer version
	onto a newer file, we refuse to touch it."""
	import json
	with _tempdir() as d:
		path = os.path.join(d, "data.json")
		with open(path, "w", encoding="utf-8") as f:
			json.dump({"version": 99, "tree": {}, "labels": {}}, f)
		tree, _labels = storage.load(path)
		assert list(tree.assigned_ids()) == []
		assert glob.glob(os.path.join(d, "data.json.corrupt-*"))
