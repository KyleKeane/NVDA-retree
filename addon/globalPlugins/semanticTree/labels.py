"""User-assigned display labels for objects whose automation name is poor.

Pure mapping from ``object_id -> str``. Persistence is handled by storage.py.
"""

from typing import Dict, Hashable, Iterable, Optional


ObjectId = Hashable


class LabelStore:
	def __init__(self) -> None:
		self._labels: Dict[ObjectId, str] = {}

	def set(self, object_id: ObjectId, label: str) -> None:
		if not label:
			self.clear(object_id)
			return
		self._labels[object_id] = label

	def clear(self, object_id: ObjectId) -> None:
		self._labels.pop(object_id, None)

	def get(self, object_id: ObjectId) -> Optional[str]:
		return self._labels.get(object_id)

	def items(self) -> Iterable:
		return self._labels.items()

	def to_dict(self) -> Dict[str, list]:
		return {
			"labels": [
				[list(oid) if isinstance(oid, tuple) else oid, text]
				for oid, text in self._labels.items()
			]
		}

	@classmethod
	def from_dict(cls, data: Dict[str, list]) -> "LabelStore":
		store = cls()
		for oid, text in data.get("labels", []):
			key = tuple(oid) if isinstance(oid, list) else oid
			store._labels[key] = text
		return store
