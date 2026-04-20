"""Dialog: live-filtered list of semantic objects, VoiceOver-style.

Types in the text box filter the list below. Arrow keys move through
matches, Enter jumps to that object (and closes the dialog). The filter
supports ``facet:value`` terms; see search.py for syntax.
"""

from collections.abc import Callable, Mapping

import gui  # type: ignore
import wx  # type: ignore

from ..labels import LabelStore
from ..search import filter_items, sort_items
from ..tree import SemanticTree
from ..walker import NVDAWalker


def _facets_for(oid, tree: SemanticTree, labels: LabelStore, walker: NVDAWalker) -> Mapping[str, object]:
	obj = walker.object_for_id(oid)
	name = getattr(obj, "name", "") if obj is not None else ""
	role = getattr(obj, "roleText", None) if obj is not None else None
	if role is None and obj is not None:
		role = str(getattr(obj, "role", "") or "")
	app = getattr(obj, "appModuleName", "") if obj is not None else ""
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
		"role": role or "",
		"app": app or "",
		"path": " > ".join(part for part in path_parts if part),
	}


def build_items(tree: SemanticTree, labels: LabelStore, walker: NVDAWalker):
	return sort_items([_facets_for(oid, tree, labels, walker) for oid in tree.assigned_ids()])


def open_search_dialog(
	tree: SemanticTree,
	labels: LabelStore,
	walker: NVDAWalker,
	on_pick: Callable[[object], None],
) -> None:
	items = build_items(tree, labels, walker)
	dlg = _SearchDialog(gui.mainFrame, items, walker)
	gui.runScriptModalDialog(dlg, lambda result: _handle(result, dlg, on_pick))


def _handle(result: int, dlg: "_SearchDialog", on_pick: Callable[[object], None]) -> None:
	if result == wx.ID_OK:
		picked = dlg.picked_object
		if picked is not None:
			on_pick(picked)
	dlg.Destroy()


class _SearchDialog(wx.Dialog):
	def __init__(self, parent, items, walker: NVDAWalker):
		super().__init__(parent, title=_("Semantic Tree: search"),
						 style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
		self._all_items = list(items)
		self._shown: list[Mapping[str, object]] = list(items)
		self._walker = walker

		sizer = wx.BoxSizer(wx.VERTICAL)
		sizer.Add(wx.StaticText(self, label=_("Search (e.g. 'button toolbar' or 'role:edit'):")),
				  flag=wx.ALL, border=8)
		self._query = wx.TextCtrl(self)
		self._query.Bind(wx.EVT_TEXT, self._on_query)
		sizer.Add(self._query, flag=wx.EXPAND | wx.ALL, border=8)
		self._list = wx.ListBox(self, style=wx.LB_SINGLE)
		self._list.Bind(wx.EVT_LISTBOX_DCLICK, lambda _e: self.EndModal(wx.ID_OK))
		sizer.Add(self._list, proportion=1, flag=wx.EXPAND | wx.ALL, border=8)
		btns = self.CreateButtonSizer(wx.OK | wx.CANCEL)
		sizer.Add(btns, flag=wx.EXPAND | wx.ALL, border=8)
		self.SetSizerAndFit(sizer)
		self.SetSize((600, 500))
		self._refresh()
		self._query.SetFocus()

	def _on_query(self, _event) -> None:
		self._shown = filter_items(self._all_items, self._query.GetValue())
		self._refresh()

	def _refresh(self) -> None:
		self._list.Set([self._format(item) for item in self._shown])
		if self._shown:
			self._list.SetSelection(0)

	@staticmethod
	def _format(item: Mapping[str, object]) -> str:
		parts = [str(item.get("label") or "")]
		role = item.get("role")
		if role:
			parts.append(f"[{role}]")
		path = item.get("path")
		if path:
			parts.append(f"— {path}")
		return " ".join(parts)

	@property
	def picked_object(self):
		index = self._list.GetSelection()
		if index == wx.NOT_FOUND or not self._shown:
			return None
		item = self._shown[index]
		return self._walker.object_for_id(item["id"])
