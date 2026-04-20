"""Filter a flat list of facet dictionaries for the item-chooser UI.

A *facet dict* describes one candidate entry and looks like::

	{
		"id":       ObjectId,
		"label":    "Custom label or automation name",
		"role":     "button",
		"app":      "firefox",
		"path":     "Window > Toolbar > Reload",
	}

The matcher splits the query on whitespace. Each term must be found
(case-insensitively) as a substring of at least one facet value. A term
prefixed with ``<facet>:`` restricts the match to that facet (e.g.
``role:button``). Negation with a leading ``-`` excludes matches.

Kept pure so the search UI can reuse it and tests can cover it without wx.
"""

from typing import Iterable, List, Mapping, Sequence


def _normalise(value: object) -> str:
	return str(value or "").lower()


def _term_matches(facets: Mapping[str, object], term: str) -> bool:
	if not term:
		return True
	if ":" in term:
		key, _, needle = term.partition(":")
		haystack = _normalise(facets.get(key, ""))
		return needle.lower() in haystack
	needle = term.lower()
	return any(needle in _normalise(v) for v in facets.values())


def matches(facets: Mapping[str, object], query: str) -> bool:
	terms = query.split()
	for term in terms:
		if term.startswith("-"):
			if _term_matches(facets, term[1:]):
				return False
		else:
			if not _term_matches(facets, term):
				return False
	return True


def filter_items(items: Iterable[Mapping[str, object]], query: str) -> List[Mapping[str, object]]:
	if not query.strip():
		return list(items)
	return [item for item in items if matches(item, query)]


def sort_items(items: Sequence[Mapping[str, object]]) -> List[Mapping[str, object]]:
	return sorted(items, key=lambda item: _normalise(item.get("label")))
