"""User-assigned display labels for objects whose automation name is poor.

Pure mapping from ``object_id -> str``. Persistence is handled by
:mod:`storage`.

Pattern matching
----------------
:meth:`LabelStore.get` does an exact dict lookup first, then a
linear pattern fallback against :func:`patterns.matches`. When
multiple stored patterns match the same live id, the most-specific
one wins (ties broken by insertion order). Exact hits always beat
any pattern, because the dict lookup runs first.
"""

from collections.abc import Hashable, Iterable

from . import patterns


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
		"""Return the label for ``object_id``.

		Exact match first, then a linear scan of stored keys that
		contain wildcards. If several patterns match, the most
		specific one (fewest wildcard slots) wins.
		"""
		if object_id in self._labels:
			return self._labels[object_id]
		best_match: tuple[int, str] | None = None
		for stored, text in self._labels.items():
			if not patterns.is_pattern(stored):
				continue
			if patterns.matches(stored, object_id):
				score = patterns.specificity(stored)
				if best_match is None or score > best_match[0]:
					best_match = (score, text)
		return best_match[1] if best_match else None

	def items(self) -> Iterable:
		return self._labels.items()

	def to_dict(self) -> dict[str, list]:
		return {
			"labels": [
				[_encode(oid), text]
				for oid, text in self._labels.items()
			]
		}

	@classmethod
	def from_dict(cls, data: dict[str, list]) -> "LabelStore":
		store = cls()
		for oid, text in data.get("labels", []):
			store._labels[_decode(oid)] = text
		return store


def _encode(value):
	"""Recursively turn tuples into lists so JSON can serialise them."""
	if isinstance(value, tuple):
		return [_encode(v) for v in value]
	return value


def _decode(value):
	"""Recursively turn JSON arrays back into tuples.

	Necessary because nested :class:`ObjectId` paths arrive as
	nested lists from :func:`json.load`, and lists are not
	hashable — a flat ``tuple(oid)`` would leave the inner path as
	an unhashable list and break every subsequent dict lookup.
	"""
	if isinstance(value, list):
		return tuple(_decode(v) for v in value)
	return value
