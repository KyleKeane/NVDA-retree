"""Tests for :class:`SemanticNavigator` using :class:`FakeWalker`.

The production navigator talks to an :class:`NVDAWalker`, but it only
touches the AccessWalker protocol plus a ``search_subtree`` fallback.
Our ``FakeWalker`` implements both, so these tests exercise the real
navigator logic end-to-end without NVDA.
"""

from semanticTree.navigator import SemanticNavigator
from semanticTree.tree import SemanticTree

from fakes import FakeObject, FakeWalker


def _build_world():
	root = FakeObject("root", "window")
	toolbar = root.add(FakeObject("toolbar", "toolbar"))
	reload_btn = toolbar.add(FakeObject("Reload", "button"))
	back_btn = toolbar.add(FakeObject("Back", "button"))
	body = root.add(FakeObject("body", "pane"))
	link = body.add(FakeObject("About", "link"))
	walker = FakeWalker()
	walker.register(root)
	return {
		"root": root,
		"toolbar": toolbar,
		"reload": reload_btn,
		"back": back_btn,
		"body": body,
		"link": link,
		"walker": walker,
	}


def _nav(tree=None):
	w = _build_world()
	nav = SemanticNavigator(tree or SemanticTree(), w["walker"])
	return nav, w


def test_parent_on_unassigned_object_returns_none():
	nav, w = _nav()
	nav.focus(w["reload"])
	assert nav.to_parent() is None


def test_parent_walks_to_explicit_ancestor():
	tree = SemanticTree()
	w = _build_world()
	tree.assign(w["walker"].id_of(w["toolbar"]), None)
	nav = SemanticNavigator(tree, w["walker"])
	nav.focus(w["reload"])
	result = nav.to_parent()
	assert result is w["toolbar"]
	assert nav.current is w["toolbar"]


def test_first_child_of_unassigned_uses_accessibility_children():
	nav, w = _nav()
	nav.focus(w["toolbar"])
	result = nav.to_first_child()
	assert result is w["reload"]


def test_first_child_of_assigned_uses_effective_children():
	tree = SemanticTree()
	w = _build_world()
	tree.assign(w["walker"].id_of(w["toolbar"]), None)
	nav = SemanticNavigator(tree, w["walker"])
	nav.focus(w["toolbar"])
	# Effective children of toolbar are its inherited accessibility kids.
	result = nav.to_first_child()
	assert result in (w["reload"], w["back"])


def test_sibling_moves_within_inherited_group():
	tree = SemanticTree()
	w = _build_world()
	tree.assign(w["walker"].id_of(w["toolbar"]), None)
	nav = SemanticNavigator(tree, w["walker"])
	nav.focus(w["reload"])
	nxt = nav.to_next_sibling()
	assert nxt is w["back"]
	prv = nav.to_previous_sibling()
	assert prv is w["reload"]


def test_sibling_move_at_boundary_returns_none():
	tree = SemanticTree()
	w = _build_world()
	tree.assign(w["walker"].id_of(w["toolbar"]), None)
	nav = SemanticNavigator(tree, w["walker"])
	nav.focus(w["reload"])
	assert nav.to_previous_sibling() is None


def test_explicit_reparent_moves_semantic_neighbourhood():
	tree = SemanticTree()
	w = _build_world()
	tree.assign(w["walker"].id_of(w["toolbar"]), None)
	tree.assign(w["walker"].id_of(w["body"]), None)
	tree.assign(w["walker"].id_of(w["reload"]), w["walker"].id_of(w["body"]))
	nav = SemanticNavigator(tree, w["walker"])
	nav.focus(w["reload"])
	parent = nav.to_parent()
	assert parent is w["body"]


def test_first_child_falls_back_to_subtree_search():
	"""After a simulated cold start, an explicit child's live object is
	not in the walker cache. The navigator must still reach it by
	searching from the anchor's root window."""
	tree = SemanticTree()
	w = _build_world()
	body_id = w["walker"].id_of(w["body"])
	reload_id = w["walker"].id_of(w["reload"])
	tree.assign(body_id, None)
	tree.assign(reload_id, body_id)

	# Drop reload from resolution but NOT from the accessibility tree.
	w["walker"].forget(w["reload"])

	nav = SemanticNavigator(tree, w["walker"])
	nav.focus(w["body"])
	result = nav.to_first_child()
	assert result is w["reload"]


def test_parent_falls_back_to_accessibility_chain():
	"""If the explicit parent's live object is lost from the cache, the
	navigator should still reach it by walking up the accessibility tree."""
	tree = SemanticTree()
	w = _build_world()
	tree.assign(w["walker"].id_of(w["toolbar"]), None)
	w["walker"].forget(w["toolbar"])
	nav = SemanticNavigator(tree, w["walker"])
	nav.focus(w["reload"])
	result = nav.to_parent()
	assert result is w["toolbar"]
