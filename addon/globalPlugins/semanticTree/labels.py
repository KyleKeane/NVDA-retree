"""User-assigned display labels for objects whose automation name is poor.

Pure mapping from ``object_id -> str``. Persistence is handled by storage.py.
"""

from collections.abc import Hashable, Iterable


ObjectId = Hashable


class LabelStore:
	def __init__(self) -> None:
		self._labels: dict[ObjectId, str] = {}

	def set(self, object_id: ObjectId, label: str) -> None:
		if not label:
			self.clear(object_id)
			return
		self._labels[object_id] = label

	def clear(self, object_id: ObjectId) -> None:
		self._labels.pop(object_id, None)

	def get(self, object_id: ObjectId) -> str | None:
		return self._labels.get(object_id)

	def items(self) -> Iterable:
		return self._labels.items()

	def to_dict(self) -> dict[str, list]:
		return {
			"labels": [
				[list(oid) if isinstance(oid, tuple) else oid, text]
				for oid, text in self._labels.items()
			]
		}

	@classmethod
	def from_dict(cls, data: dict[str, list]) -> "LabelStore":
		store = cls()
		for oid, text in data.get("labels", []):
			key = tuple(oid) if isinstance(oid, list) else oid
			store._labels[key] = text
		return store
