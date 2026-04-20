"""Pure facet extraction used by the search UI.

Split out of ``ui/search.py`` so it has no wx dependency and can be
unit-tested directly. Returns a facet dictionary shaped for the
matcher in ``search.py``.
"""

from collections.abc import Mapping
from typing import Any

from .labels import LabelStore
from .tree import SemanticTree


def app_name(obj: Any) -> str:
	if obj is None:
		return ""
	app_module = getattr(obj, "appModule", None)
	if app_module is None:
		return ""
	return str(getattr(app_module, "appName", "") or "")


def role_text(obj: Any) -> str:
	if obj is None:
		return ""
	text = getattr(obj, "roleText", None)
	if text:
		return str(text)
	role = getattr(obj, "role", None)
	return str(role) if role is not None else ""


def facets_for(oid, tree: SemanticTree, labels: LabelStore, walker) -> Mapping[str, object]:
	obj = walker.object_for_id(oid)
	name = getattr(obj, "name", "") if obj is not None else ""
	label = labels.get(oid) or name or str(oid)
	path_parts: list[str] = []
	current = oid
	while current is not None:
		current = tree.parent_of(current)
		if current is None:
			break
		path_parts.append(labels.get(current) or "")
	path_parts.reverse()
	return {
		"id": oid,
		"label": label,
		"role": role_text(obj),
		"app": app_name(obj),
		"path": " > ".join(part for part in path_parts if part),
	}


def build_items(tree: SemanticTree, labels: LabelStore, walker):
	"""All facet dicts for every assigned id, sorted by label."""
	from .search import sort_items
	return sort_items([facets_for(oid, tree, labels, walker) for oid in tree.assigned_ids()])
