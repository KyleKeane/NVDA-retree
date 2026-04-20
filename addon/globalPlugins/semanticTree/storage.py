"""JSON persistence for the semantic tree and label store.

Stored as a single JSON document::

    {
        "version": 1,
        "tree":   {"assignments": [[child_id, parent_id], ...]},
        "labels": {"labels":      [[object_id, text], ...]}
    }

IDs are tuples in memory but are serialised as JSON arrays. The
``from_dict`` methods on :class:`SemanticTree` and :class:`LabelStore`
convert them back.

If the file on disk is unreadable or malformed, :func:`load` renames it
aside with a ``.corrupt-<timestamp>`` suffix and returns empty stores so
the add-on can keep running. Saves are atomic (``os.replace``).
"""

import json
import os
import time

from .labels import LabelStore
from .tree import SemanticTree


SCHEMA_VERSION = 1


def load(path: str) -> tuple[SemanticTree, LabelStore]:
	if not os.path.exists(path):
		return SemanticTree(), LabelStore()
	try:
		with open(path, encoding="utf-8") as f:
			data = json.load(f)
	except (OSError, ValueError) as exc:
		_quarantine(path, f"could not read: {exc}")
		return SemanticTree(), LabelStore()
	if not isinstance(data, dict):
		_quarantine(path, "top-level JSON is not an object")
		return SemanticTree(), LabelStore()
	try:
		tree = SemanticTree.from_dict(data.get("tree") or {})
		labels = LabelStore.from_dict(data.get("labels") or {})
	except Exception as exc:
		_quarantine(path, f"could not decode contents: {exc}")
		return SemanticTree(), LabelStore()
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


def _quarantine(path: str, reason: str) -> None:
	backup = f"{path}.corrupt-{int(time.time())}"
	try:
		os.replace(path, backup)
	except OSError:
		# The user will see empty state but nothing worse.
		return
	try:
		import logging

		logging.getLogger(__name__).warning(
			"semanticTree: quarantined unreadable state at %s (%s); backup at %s",
			path, reason, backup,
		)
	except Exception:
		pass
