"""Compute the effective semantic parent and children of an object.

The semantic tree only stores explicit assignments. Everything else is
inherited from the nearest explicit ancestor in the accessibility tree.

Effective parent
----------------
For an object X:
  1. If X is explicitly assigned, its effective parent is its explicit parent.
  2. Otherwise, walk up X's accessibility-tree ancestors. The first one that
     is explicitly assigned is X's effective parent.
  3. If no ancestor is assigned, X has no effective parent (it is outside
     the semantic tree).

Effective children of P (an explicitly-assigned object):
  * Every object X whose effective parent (by the rule above) is P.

The walker is written against a small abstract interface (``AccessWalker``)
so it can be driven by real NVDA objects in production and by stubs in
tests.
"""

from typing import Any, Iterable, List, Optional, Protocol

from .tree import ObjectId, SemanticTree


class AccessWalker(Protocol):
	"""How to traverse the accessibility tree and identify objects."""

	def id_of(self, obj: Any) -> Optional[ObjectId]: ...
	def parent_of(self, obj: Any) -> Optional[Any]: ...
	def children_of(self, obj: Any) -> Iterable[Any]: ...
	def object_for_id(self, object_id: ObjectId) -> Optional[Any]: ...


def effective_parent(obj: Any, tree: SemanticTree, walker: AccessWalker) -> Optional[ObjectId]:
	oid = walker.id_of(obj)
	if oid is None:
		return None
	if tree.is_assigned(oid):
		return tree.parent_of(oid)
	ancestor = walker.parent_of(obj)
	while ancestor is not None:
		aid = walker.id_of(ancestor)
		if aid is not None and tree.is_assigned(aid):
			return aid
		ancestor = walker.parent_of(ancestor)
	return None


def effective_children(parent_id: Optional[ObjectId], tree: SemanticTree, walker: AccessWalker) -> List[ObjectId]:
	"""Return the ordered IDs of effective children under ``parent_id``.

	Order:
	  * Explicit assignments first (in insertion order).
	  * Then inherited descendants, in accessibility-tree order.

	``parent_id=None`` returns the semantic roots plus any object whose
	accessibility-tree root has no explicit ancestor (these are typically
	not useful, so the caller normally only passes assigned IDs).
	"""
	seen: set = set()
	result: List[ObjectId] = []

	for cid in tree.explicit_children(parent_id):
		if cid not in seen:
			seen.add(cid)
			result.append(cid)

	if parent_id is None:
		return result

	parent_obj = walker.object_for_id(parent_id)
	if parent_obj is None:
		return result

	for descendant_id in _inherited_descendants(parent_obj, parent_id, tree, walker):
		if descendant_id not in seen:
			seen.add(descendant_id)
			result.append(descendant_id)

	return result


def _inherited_descendants(parent_obj: Any, parent_id: ObjectId, tree: SemanticTree, walker: AccessWalker) -> Iterable[ObjectId]:
	for child_obj in walker.children_of(parent_obj):
		cid = walker.id_of(child_obj)
		if cid is None:
			continue
		if tree.is_assigned(cid):
			# The explicit assignment wins; this child and its subtree
			# are placed wherever the user put them, not here.
			continue
		yield cid
		yield from _inherited_descendants(child_obj, parent_id, tree, walker)
