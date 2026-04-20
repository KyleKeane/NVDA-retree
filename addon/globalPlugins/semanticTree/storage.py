"""JSON persistence for the semantic tree and label store.

Stored as a single JSON document::

	{
		"version": 1,
		"tree":   {"assignments": [[child_id, parent_id], ...]},
		"labels": {"labels":      [[object_id, text], ...]}
	}

IDs are tuples in memory but are serialised as JSON arrays. The ``from_dict``
methods on :class:`SemanticTree` and :class:`LabelStore` convert them back.
"""

import json
import os
from typing import Tuple

from .labels import LabelStore
from .tree import SemanticTree


SCHEMA_VERSION = 1


def load(path: str) -> Tuple[SemanticTree, LabelStore]:
	if not os.path.exists(path):
		return SemanticTree(), LabelStore()
	with open(path, "r", encoding="utf-8") as f:
		data = json.load(f)
	tree = SemanticTree.from_dict(data.get("tree", {}))
	labels = LabelStore.from_dict(data.get("labels", {}))
	return tree, labels


def save(path: str, tree: SemanticTree, labels: LabelStore) -> None:
	directory = os.path.dirname(path)
	if directory:
		os.makedirs(directory, exist_ok=True)
	payload = {
		"version": SCHEMA_VERSION,
		"tree": tree.to_dict(),
		"labels": labels.to_dict(),
	}
	tmp = path + ".tmp"
	with open(tmp, "w", encoding="utf-8") as f:
		json.dump(payload, f, indent="\t", ensure_ascii=False)
	os.replace(tmp, path)
