"""The semantic tree: a record of user-made parent reassignments.

We only store *explicit* assignments. An object that the user has never
touched is not in this structure at all; its position is inherited at
lookup time (see inheritance.py). That keeps this module tiny and makes
moves O(1).

Data model
----------
Each assignment maps ``child_id -> parent_id``. ``parent_id`` may be
``None`` to mean "this object is a semantic root".

Invariants enforced here:
* No cycles: you cannot make an object its own ancestor.
* An object has at most one explicit parent.

Everything else (what children an object has, iteration order, etc.) is
derived on demand and lives elsewhere.
"""

from collections.abc import Hashable, Iterable, Iterator

from . import patterns


ObjectId = Hashable


class CycleError(ValueError):
	"""Raised when an assignment would create a cycle."""


class SemanticTree:
	def __init__(self) -> None:
		self._parent: dict[ObjectId, ObjectId | None] = {}

	def assign(self, child_id: ObjectId, parent_id: ObjectId | None) -> None:
		if child_id is None:
			raise ValueError("child_id must not be None")
		if patterns.is_pattern(child_id) or patterns.is_pattern(parent_id):
			raise ValueError(
				"Semantic-tree assignments cannot contain wildcards yet; "
				"V1 pattern matching is only supported on labels."
			)
		if parent_id is not None and self._would_cycle(child_id, parent_id):
			raise CycleError(f"Assigning {child_id!r} under {parent_id!r} would create a cycle")
		self._parent[child_id] = parent_id

	def unassign(self, child_id: ObjectId) -> None:
		self._parent.pop(child_id, None)

	def is_assigned(self, child_id: ObjectId) -> bool:
		return child_id in self._parent

	def parent_of(self, child_id: ObjectId) -> ObjectId | None:
		return self._parent.get(child_id)

	def explicit_children(self, parent_id: ObjectId | None) -> list[ObjectId]:
		return [cid for cid, pid in self._parent.items() if pid == parent_id]

	def roots(self) -> list[ObjectId]:
		return self.explicit_children(None)

	def assigned_ids(self) -> Iterable[ObjectId]:
		return self._parent.keys()

	def explicit_descendants(self, root_id: ObjectId) -> set:
		"""All IDs currently explicitly parented under ``root_id`` (transitively).

		Does not include ``root_id`` itself. Breaks cycles defensively
		(the tree shouldn't contain any, but a hand-edited state file
		might).
		"""
		result: set = set()
		stack = [root_id]
		while stack:
			current = stack.pop()
			for child in self.explicit_children(current):
				if child in result:
					continue
				result.add(child)
				stack.append(child)
		return result

	def ancestors(self, child_id: ObjectId) -> Iterator[ObjectId]:
		seen: set = set()
		current = self._parent.get(child_id)
		while current is not None and current not in seen:
			seen.add(current)
			yield current
			current = self._parent.get(current)

	def _would_cycle(self, child_id: ObjectId, new_parent_id: ObjectId) -> bool:
		if child_id == new_parent_id:
			return True
		# Walk up from new_parent_id. If we pass through child_id, cycle.
		current: ObjectId | None = new_parent_id
		seen: set = set()
		while current is not None and current not in seen:
			if current == child_id:
				return True
			seen.add(current)
			current = self._parent.get(current)
		return False

	def to_dict(self) -> dict[str, list]:
		return {
			"assignments": [
				[_encode(c), _encode(p)] for c, p in self._parent.items()
			],
		}

	@classmethod
	def from_dict(cls, data: dict[str, list]) -> "SemanticTree":
		tree = cls()
		for child, parent in data.get("assignments", []):
			tree._parent[_decode(child)] = _decode(parent)
		return tree


def _encode(value):
	"""Recursively turn tuples into lists so JSON can serialise them."""
	if isinstance(value, tuple):
		return [_encode(v) for v in value]
	return value


def _decode(value):
	"""Recursively turn JSON arrays back into tuples.

	Nested :class:`ObjectId` paths arrive as nested lists from
	:func:`json.load`, and lists are not hashable — a flat
	``tuple(oid)`` would leave the inner path as an unhashable
	list and break every subsequent dict lookup.
	"""
	if isinstance(value, list):
		return tuple(_decode(v) for v in value)
	return value
