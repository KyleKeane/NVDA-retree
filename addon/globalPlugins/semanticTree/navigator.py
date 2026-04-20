"""Semantic cursor: tracks the object currently focused in the semantic tree
and moves it under the four directional gestures.

A move returns the new focus (an NVDA object) or ``None`` if the move is
not possible (e.g. no parent, no siblings). The caller is responsible for
reporting the result to the user and for syncing NVDA's own navigator
object; :func:`sync_nvda_navigator` does the latter.

The cursor uses an *anchor* object to resolve inherited positions: we
never ask "give me the nth child of id X" in isolation, we always ask
"starting from this live object, walk the semantic tree". That keeps us
robust when objects we have never seen live are referenced by assignment.
"""

from typing import Any

from .inheritance import effective_children, effective_parent
from .tree import ObjectId, SemanticTree
from .walker import NVDAWalker


class SemanticNavigator:
	def __init__(self, tree: SemanticTree, walker: NVDAWalker) -> None:
		self._tree = tree
		self._walker = walker
		self._current: Any | None = None

	@property
	def current(self) -> Any | None:
		return self._current

	def focus(self, obj: Any | None) -> None:
		self._current = obj
		if obj is not None:
			self._walker.remember(obj)

	def to_parent(self) -> Any | None:
		if self._current is None:
			return None
		pid = effective_parent(self._current, self._tree, self._walker)
		if pid is None:
			return None
		parent_obj = self._walker.object_for_id(pid)
		if parent_obj is None:
			# Fall back to the accessibility-tree parent chain, which is
			# cheap and usually reaches the same object.
			ancestor = self._walker.parent_of(self._current)
			while ancestor is not None and self._walker.id_of(ancestor) != pid:
				ancestor = self._walker.parent_of(ancestor)
			parent_obj = ancestor
		if parent_obj is not None:
			self.focus(parent_obj)
		return parent_obj

	def to_first_child(self) -> Any | None:
		if self._current is None:
			return None
		cid = self._walker.id_of(self._current)
		if cid is None:
			return None
		if not self._tree.is_assigned(cid):
			# If the current node is not itself assigned, its semantic
			# children (inherited) are just its accessibility children.
			for child in self._walker.children_of(self._current):
				self.focus(child)
				return child
			return None
		children_ids = effective_children(cid, self._tree, self._walker)
		return self._focus_by_id(children_ids[0]) if children_ids else None

	def to_next_sibling(self) -> Any | None:
		return self._sibling_move(offset=+1)

	def to_previous_sibling(self) -> Any | None:
		return self._sibling_move(offset=-1)

	def _sibling_move(self, offset: int) -> Any | None:
		if self._current is None:
			return None
		siblings = self._sibling_ids()
		cid = self._walker.id_of(self._current)
		if cid is None or cid not in siblings:
			return None
		index = siblings.index(cid) + offset
		if index < 0 or index >= len(siblings):
			return None
		return self._focus_by_id(siblings[index])

	def _sibling_ids(self) -> list[ObjectId]:
		parent_id = effective_parent(self._current, self._tree, self._walker)
		if parent_id is None:
			return list(self._tree.roots())
		return effective_children(parent_id, self._tree, self._walker)

	def _focus_by_id(self, oid: ObjectId) -> Any | None:
		obj = self._walker.object_for_id(oid)
		if obj is None:
			obj = self._resolve_via_search(oid)
		if obj is None:
			return None
		self.focus(obj)
		return obj

	def _resolve_via_search(self, oid: ObjectId) -> Any | None:
		"""Best-effort fallback when the cache has lost the live object.

		Walks up from the current anchor to the foreground window and
		searches a bounded subtree under it. Covers the common case of a
		persisted assignment whose object existed at save time but has
		not been seen live in this session.
		"""
		anchor = self._current
		if anchor is None:
			return None
		root = anchor
		steps = 0
		while steps < 50:
			parent = self._walker.parent_of(root)
			if parent is None:
				break
			root = parent
			steps += 1
		return self._walker.search_subtree(root, oid)


def sync_nvda_navigator(obj: Any) -> None:
	"""Move NVDA's own navigator object to ``obj``.

	Kept as a separate function so the rest of navigator.py has no direct
	dependency on NVDA's ``api`` module (and can be imported in tests).
	"""
	if obj is None:
		return
	try:
		import api  # type: ignore
	except Exception:
		return
	api.setNavigatorObject(obj)
