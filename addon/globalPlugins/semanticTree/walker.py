"""NVDA-backed implementation of :class:`inheritance.AccessWalker`.

This is the only module that talks to real NVDAObjects inside the core
logic. UI and gesture handling also import NVDA modules, but the core
algorithms go through this walker so that they remain testable.

Object identity resolution
--------------------------
``object_for_id`` is inherently best-effort: NVDA does not expose a way
to look up an arbitrary object from an opaque ID. We keep a weakref
cache of objects we have seen recently. Callers should:

* Call :meth:`prime_ancestors` when anchoring to a new navigator object
  so that up-moves from it can resolve IDs.
* Call :meth:`search_subtree` before giving up on an unresolved ID; it
  walks a bounded portion of the live accessibility tree looking for a
  match and populates the cache as it goes.
"""

import weakref
from collections import deque
from collections.abc import Iterable
from typing import Any

from .identity import get_object_id
from .tree import ObjectId


_PRIME_ANCESTORS_LIMIT = 50
_SEARCH_DEFAULT_MAX_DEPTH = 4
_SEARCH_DEFAULT_MAX_NODES = 500


class NVDAWalker:
	def __init__(self) -> None:
		self._cache: dict[ObjectId, weakref.ref] = {}

	def remember(self, obj: Any) -> None:
		oid = self.id_of(obj)
		if oid is None:
			return
		try:
			self._cache[oid] = weakref.ref(obj)
		except TypeError:
			# Some NVDA objects may not support weak references; drop.
			pass

	def id_of(self, obj: Any) -> ObjectId | None:
		oid = get_object_id(obj)
		if oid is not None and hasattr(obj, "__weakref__"):
			try:
				self._cache.setdefault(oid, weakref.ref(obj))
			except TypeError:
				pass
		return oid

	def parent_of(self, obj: Any) -> Any | None:
		if obj is None:
			return None
		parent = getattr(obj, "parent", None)
		if parent is not None:
			self.remember(parent)
		return parent

	def children_of(self, obj: Any) -> Iterable[Any]:
		if obj is None:
			return
		children = getattr(obj, "children", None)
		if children is None:
			return
		for child in children:
			self.remember(child)
			yield child

	def object_for_id(self, object_id: ObjectId) -> Any | None:
		ref = self._cache.get(object_id)
		if ref is None:
			return None
		obj = ref()
		if obj is None:
			self._cache.pop(object_id, None)
		return obj

	def prime_ancestors(self, obj: Any, limit: int = _PRIME_ANCESTORS_LIMIT) -> None:
		"""Populate the cache with the ancestor chain of ``obj``."""
		current = obj
		steps = 0
		while current is not None and steps < limit:
			self.remember(current)
			current = getattr(current, "parent", None)
			steps += 1

	def search_subtree(
		self,
		root: Any,
		target_id: ObjectId,
		max_depth: int = _SEARCH_DEFAULT_MAX_DEPTH,
		max_nodes: int = _SEARCH_DEFAULT_MAX_NODES,
	) -> Any | None:
		"""Breadth-first search under ``root`` for an object with ``target_id``.

		Bounded by depth and node count so we never stall NVDA on a huge
		tree. Populates the cache as it goes, so subsequent lookups are
		free. Returns ``None`` if the target is not reached within the
		budget.
		"""
		if root is None or target_id is None:
			return None
		queue: deque[tuple[Any, int]] = deque([(root, 0)])
		visited = 0
		while queue and visited < max_nodes:
			obj, depth = queue.popleft()
			visited += 1
			oid = self.id_of(obj)
			if oid == target_id:
				return obj
			if depth >= max_depth:
				continue
			for child in getattr(obj, "children", None) or ():
				queue.append((child, depth + 1))
		return None
