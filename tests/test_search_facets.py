"""Tests for facet extraction (the pure part of the search UI)."""

from semanticTree.facets import app_name, build_items, facets_for, role_text
from semanticTree.labels import LabelStore
from semanticTree.tree import SemanticTree

from fakes import FakeObject, FakeWalker


def test_app_name_reads_nested_attribute():
	obj = FakeObject("X", app_name="firefox")
	assert app_name(obj) == "firefox"


def test_app_name_safe_when_appmodule_missing():
	obj = FakeObject("X")
	del obj.appModule
	assert app_name(obj) == ""


def test_role_text_prefers_roleText_attribute():
	obj = FakeObject("X", role="button")
	obj.roleText = "push button"
	assert role_text(obj) == "push button"


def test_role_text_falls_back_to_role():
	obj = FakeObject("X", role="link")
	assert role_text(obj) == "link"


def test_role_text_prefers_display_string_on_enum_role():
	"""Modern NVDA uses a Role enum whose ``displayString`` gives the
	localised label. We should prefer it over ``str(role)`` which would
	otherwise render something like 'Role.BUTTON'."""

	class FakeRole:
		displayString = "push button"

		def __str__(self):
			return "Role.BUTTON"

	obj = FakeObject("X")
	obj.role = FakeRole()
	assert role_text(obj) == "push button"


def test_facets_populated_for_real_lookup():
	obj = FakeObject("Reload", role="button", app_name="firefox")
	walker = FakeWalker()
	walker.register(obj)
	tree = SemanticTree()
	tree.assign(walker.id_of(obj), None)
	labels = LabelStore()
	labels.set(walker.id_of(obj), "Refresh page")

	facets = facets_for(walker.id_of(obj), tree, labels, walker)
	assert facets["label"] == "Refresh page"
	assert facets["role"] == "button"
	assert facets["app"] == "firefox"
	assert facets["id"] == walker.id_of(obj)


def test_build_items_sorted_by_label():
	root = FakeObject("r", "window")
	a = root.add(FakeObject("Apple", role="button"))
	z = root.add(FakeObject("Zulu", role="button"))
	m = root.add(FakeObject("Mango", role="button"))
	walker = FakeWalker()
	walker.register(root)
	tree = SemanticTree()
	for obj in (a, z, m):
		tree.assign(walker.id_of(obj), None)

	items = build_items(tree, LabelStore(), walker)
	assert [item["label"] for item in items] == ["Apple", "Mango", "Zulu"]
