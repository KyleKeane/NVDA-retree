"""Pattern matching for :class:`~semanticTree.identity.ObjectId`.

Today every ID returned by :func:`identity.get_object_id` is an
*exact* tuple of strings and integers — no wildcards. This module
lets stored IDs in user data carry ``None`` in certain slots to
mean "match any value there". That turns stored identities into
small structural patterns so a label or assignment can survive a
button being renamed, or a sibling being re-ordered, without the
user having to redo their work.

Design rule
-----------
Only *stored* IDs may contain wildcards. IDs produced by
``identity.get_object_id`` from a live NVDAObject are always
exact. :func:`matches` is therefore asymmetric: ``None`` slots in
``stored`` match anything in ``live``; ``live`` is expected to be
concrete.

Wildcards allowed:

* per-node ``discriminator`` (the second slot of each
  ``NodeSignature``)
* per-node ``sibling_index`` (the third slot)

Wildcards **not** allowed (either by convention or by the
enforcement in :func:`matches`):

* ``app_name`` — a label with no app is nonsensical.
* ``role`` — role changes are semantically meaningful; a button
  turning into a static text should be a different identity.
* ``path length`` — no ``**`` / skip-level wildcards in v1.

V1 exposes a single transform helper, :func:`name_agnostic`,
which wildcards the leaf node's discriminator. Broader transforms
(whole-path, regex) are left as explicit follow-up work.
"""

from __future__ import annotations


WILDCARD = None


def matches(stored, live) -> bool:
	"""Return True if ``stored`` describes ``live``.

	``stored`` may contain ``WILDCARD`` (``None``) in per-node
	``discriminator`` or ``sibling_index`` slots. ``live`` must be
	an exact ID from :func:`identity.get_object_id`.

	Short-circuits on app-name mismatch before any path work —
	typical case when scanning the label store is that most entries
	belong to other apps.
	"""
	if not _is_id_tuple(stored) or not _is_id_tuple(live):
		return False
	stored_app, stored_path = stored[0], stored[1]
	live_app, live_path = live[0], live[1]
	if stored_app != live_app:
		return False
	if len(stored_path) != len(live_path):
		return False
	for s_node, l_node in zip(stored_path, live_path):
		if not _node_matches(s_node, l_node):
			return False
	return True


def _node_matches(s_node, l_node) -> bool:
	# NodeSignature = (role, discriminator, sibling_index)
	if len(s_node) != 3 or len(l_node) != 3:
		return False
	s_role, s_disc, s_idx = s_node
	l_role, l_disc, l_idx = l_node
	if s_role != l_role:
		return False  # role is locked; never wildcardable.
	if s_disc is not WILDCARD and s_disc != l_disc:
		return False
	if s_idx is not WILDCARD and s_idx != l_idx:
		return False
	return True


def is_pattern(obj_id) -> bool:
	"""True iff ``obj_id`` contains at least one ``WILDCARD`` slot.

	Used as a guard — see :meth:`SemanticTree.assign`, which refuses
	patterns in v1 because the navigator cannot yet resolve a
	wildcard parent / child to a live object.
	"""
	if not _is_id_tuple(obj_id):
		return False
	_, path = obj_id
	for node in path:
		if len(node) != 3:
			continue
		_, disc, idx = node
		if disc is WILDCARD or idx is WILDCARD:
			return True
	return False


def specificity(obj_id) -> int:
	"""Count of concrete (non-wildcard) slots in ``obj_id``.

	Higher value = more specific. Used to rank pattern matches so
	the most-specific stored entry beats a looser one when both
	apply to the same live object.
	"""
	if not _is_id_tuple(obj_id):
		return 0
	_, path = obj_id
	score = 0
	for node in path:
		if len(node) != 3:
			continue
		_, disc, idx = node
		if disc is not WILDCARD:
			score += 1
		if idx is not WILDCARD:
			score += 1
	return score


def name_agnostic(obj_id):
	"""Return a copy of ``obj_id`` whose leaf node has its
	``discriminator`` wildcarded.

	This is the V1 "ignore name changes" transform — the only
	pattern shape the label dialog can produce today. Operates on
	the last node in the path; leaves the app name and every
	ancestor alone.
	"""
	if not _is_id_tuple(obj_id):
		return obj_id
	app, path = obj_id
	if not path:
		return obj_id
	leaf = path[-1]
	if len(leaf) != 3:
		return obj_id
	role, _disc, idx = leaf
	new_leaf = (role, WILDCARD, idx)
	return (app, tuple(path[:-1]) + (new_leaf,))


def _is_id_tuple(obj_id) -> bool:
	"""True if ``obj_id`` has the (app, path) shape identity.py produces."""
	return (
		isinstance(obj_id, tuple)
		and len(obj_id) == 2
		and isinstance(obj_id[1], tuple)
	)
