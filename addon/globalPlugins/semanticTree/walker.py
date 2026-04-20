"""NVDA-backed implementation of :class:`inheritance.AccessWalker`.

This is the only module that talks to real NVDAObjects inside the core
logic. UI and gesture handling also import NVDA modules, but the core
algorithms go through this walker so that they remain testable.

``object_for_id`` is inherently best-effort: NVDA does not expose a way to
look up an arbitrary object from an opaque ID. We keep a weak cache of
objects we have seen recently (usually the current focus and its
ancestors), and fall back to ``None`` if we cannot resolve an ID. Semantic
navigation is always driven from an anchor object (the current navigator)
whose accessibility tree we walk directly, so the cache only needs to
resolve IDs on that live path.
"""

import weakref
from collections.abc import Iterable
from typing import Any

from .identity import get_object_id
from .tree import ObjectId


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
