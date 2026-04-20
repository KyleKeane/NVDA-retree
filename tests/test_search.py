from semanticTree.search import filter_items, matches


ITEMS = [
	{"id": 1, "label": "Reload", "role": "button", "app": "firefox", "path": "Window > Toolbar"},
	{"id": 2, "label": "Back", "role": "button", "app": "firefox", "path": "Window > Toolbar"},
	{"id": 3, "label": "Address bar", "role": "edit", "app": "firefox", "path": "Window"},
	{"id": 4, "label": "Reload", "role": "menuitem", "app": "notepad", "path": "File"},
]


def test_empty_query_returns_all():
	assert filter_items(ITEMS, "") == ITEMS


def test_single_term_matches_substring():
	result = filter_items(ITEMS, "reload")
	assert {item["id"] for item in result} == {1, 4}


def test_multi_term_is_conjunctive():
	result = filter_items(ITEMS, "reload firefox")
	assert [item["id"] for item in result] == [1]


def test_facet_scoped_term():
	result = filter_items(ITEMS, "role:edit")
	assert [item["id"] for item in result] == [3]


def test_negation():
	result = filter_items(ITEMS, "reload -notepad")
	assert [item["id"] for item in result] == [1]


def test_case_insensitive():
	assert matches(ITEMS[0], "RELOAD")
