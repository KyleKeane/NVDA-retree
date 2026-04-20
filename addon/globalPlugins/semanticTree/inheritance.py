"""Compute the effective semantic parent and children of an object.

The semantic tree stores only *explicit* assignments. Everything else is
inherited structurally from the accessibility tree.

Model
-----
An object is "in the semantic tree" when either:
  * it is explicitly assigned, OR
  * its accessibility parent is in the semantic tree (recursively).

The effective parent of an object is:
  * its explicit parent, if it is assigned; else
  * its accessibility parent, if that accessibility parent is in the
    semantic tree; else
  * ``None`` (the object is outside the semantic tree).

The effective children of an assigned object P are:
  * the objects that the user has explicitly parented under P, then
  * the direct accessibility children of P that are not themselves
    explicitly assigned somewhere else.

This preserves the accessibility structure *inside* an assigned
subtree. Moving ``body`` to a new position brings its whole subtree
with it: ``body > container > link > span`` stays
``body > container > link > span`` in the semantic view, not flattened
into ``body > {container, link, span}``.

The walker is written against a small abstract interface
(``AccessWalker``) so it can be driven by real NVDA objects in
production and by stubs in tests.
"""

from collections.abc import Iterable
from typing import Any, Protocol

from .tree import ObjectId, SemanticTree


class AccessWalker(Protocol):
	"""How to traverse the accessibility tree and identify objects."""

	def id_of(self, obj: Any) -> ObjectId | None: ...
	def parent_of(self, obj: Any) -> Any | None: ...
	def children_of(self, obj: Any) -> Iterable[Any]: ...
	def object_for_id(self, object_id: ObjectId) -> Any | None: ...


def _is_in_semantic_tree(obj: Any, tree: SemanticTree, walker: AccessWalker) -> bool:
	"""Walk up the accessibility parents, returning True when we hit an
	explicitly assigned ancestor (or ``obj`` itself is assigned)."""
	current = obj
	steps = 0
	while current is not None and steps < 256:
		oid = walker.id_of(current)
		if oid is not None and tree.is_assigned(oid):
			return True
		current = walker.parent_of(current)
		steps += 1
	return False


def effective_parent(obj: Any, tree: SemanticTree, walker: AccessWalker) -> ObjectId | None:
	oid = walker.id_of(obj)
	if oid is None:
		return None
	if tree.is_assigned(oid):
		return tree.parent_of(oid)
	acc_parent = walker.parent_of(obj)
	if acc_parent is None:
		return None
	if not _is_in_semantic_tree(acc_parent, tree, walker):
		return None
	return walker.id_of(acc_parent)


def effective_children(
	parent_id: ObjectId | None,
	tree: SemanticTree,
	walker: AccessWalker,
) -> list[ObjectId]:
	"""Return the ordered IDs of effective children under ``parent_id``.

	Order:
	  * explicit assignments first (insertion order), then
	  * direct accessibility children of the live parent object, skipping
	    any that are explicitly assigned somewhere (including under this
	    same parent — avoids duplicates).

	``parent_id=None`` returns the explicit semantic roots. In that case
	we cannot meaningfully list "inherited roots" because every live
	object that isn't assigned has no effective parent of None; those
	objects are simply outside the semantic tree.
	"""
	seen: set = set()
	result: list[ObjectId] = []

	for cid in tree.explicit_children(parent_id):
		if cid not in seen:
			seen.add(cid)
			result.append(cid)

	if parent_id is None:
		return result

	parent_obj = walker.object_for_id(parent_id)
	if parent_obj is None:
		return result

	for child_obj in walker.children_of(parent_obj):
		cid = walker.id_of(child_obj)
		if cid is None or cid in seen:
			continue
		if tree.is_assigned(cid):
			# Explicit assignment wins; this child lives wherever the
			# user put it, not in its accessibility position.
			continue
		seen.add(cid)
		result.append(cid)

	return result
