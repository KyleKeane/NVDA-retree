from semanticTree.inheritance import effective_children, effective_parent
from semanticTree.tree import SemanticTree

from fakes import FakeObject, FakeWalker


def _world():
	root = FakeObject("root", "window")
	toolbar = root.add(FakeObject("toolbar", "toolbar"))
	reload_btn = toolbar.add(FakeObject("Reload", "button"))
	back_btn = toolbar.add(FakeObject("Back", "button"))
	body = root.add(FakeObject("body", "pane"))
	link = body.add(FakeObject("About", "link"))
	walker = FakeWalker()
	walker.register(root)
	return root, toolbar, reload_btn, back_btn, body, link, walker


def test_inherits_from_nearest_explicit_ancestor():
	root, toolbar, reload_btn, back_btn, body, link, walker = _world()
	tree = SemanticTree()
	tree.assign(walker.id_of(toolbar), None)
	assert effective_parent(reload_btn, tree, walker) == walker.id_of(toolbar)
	assert effective_parent(back_btn, tree, walker) == walker.id_of(toolbar)
	assert effective_parent(link, tree, walker) is None


def test_explicit_override_wins():
	root, toolbar, reload_btn, back_btn, body, link, walker = _world()
	tree = SemanticTree()
	tree.assign(walker.id_of(toolbar), None)
	tree.assign(walker.id_of(body), None)
	tree.assign(walker.id_of(reload_btn), walker.id_of(body))
	assert effective_parent(reload_btn, tree, walker) == walker.id_of(body)
	# The other toolbar child still inherits from the toolbar.
	assert effective_parent(back_btn, tree, walker) == walker.id_of(toolbar)


def test_effective_children_mixes_explicit_and_inherited():
	root, toolbar, reload_btn, back_btn, body, link, walker = _world()
	tree = SemanticTree()
	tree.assign(walker.id_of(toolbar), None)
	children = effective_children(walker.id_of(toolbar), tree, walker)
	assert walker.id_of(reload_btn) in children
	assert walker.id_of(back_btn) in children


def test_explicit_subtree_not_double_counted():
	"""A child that the user has moved elsewhere should NOT also appear
	as an inherited child of its original parent."""
	root, toolbar, reload_btn, back_btn, body, link, walker = _world()
	tree = SemanticTree()
	tree.assign(walker.id_of(toolbar), None)
	tree.assign(walker.id_of(body), None)
	tree.assign(walker.id_of(reload_btn), walker.id_of(body))
	toolbar_kids = effective_children(walker.id_of(toolbar), tree, walker)
	assert walker.id_of(reload_btn) not in toolbar_kids
	assert walker.id_of(back_btn) in toolbar_kids
	body_kids = effective_children(walker.id_of(body), tree, walker)
	assert walker.id_of(reload_btn) in body_kids
