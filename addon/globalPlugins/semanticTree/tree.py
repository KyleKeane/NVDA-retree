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


ObjectId = Hashable


class CycleError(ValueError):
	"""Raised when an assignment would create a cycle."""


class SemanticTree:
	def __init__(self) -> None:
		self._parent: dict[ObjectId, ObjectId | None] = {}

	def assign(self, child_id: ObjectId, parent_id: ObjectId | None) -> None:
		if child_id is None:
			raise ValueError("child_id must not be None")
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
		def encode(value):
			return list(value) if isinstance(value, tuple) else value

		return {
			"assignments": [[encode(c), encode(p)] for c, p in self._parent.items()],
		}

	@classmethod
	def from_dict(cls, data: dict[str, list]) -> "SemanticTree":
		tree = cls()
		for child, parent in data.get("assignments", []):
			c = tuple(child) if isinstance(child, list) else child
			p = tuple(parent) if isinstance(parent, list) else parent
			tree._parent[c] = p
		return tree
