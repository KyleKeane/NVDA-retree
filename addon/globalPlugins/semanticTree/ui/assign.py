"""Dialog: pick a semantic parent for the given child.

Shows the current semantic tree as a wx.TreeCtrl of already-assigned
objects plus a synthetic "(top level)" entry. Arrow keys walk the
tree. Enter confirms, Escape cancels. The object being assigned and
its current descendants are hidden as candidate parents to prevent
cycles.
"""

from collections.abc import Callable

import gui  # type: ignore
import wx  # type: ignore

from ..labels import LabelStore
from ..tree import ObjectId, SemanticTree
from ..walker import NVDAWalker


def open_assign_dialog(
	child_id: ObjectId,
	tree: SemanticTree,
	labels: LabelStore,
	walker: NVDAWalker,
	on_commit: Callable[[ObjectId | None], None],
) -> None:
	dlg = _AssignDialog(gui.mainFrame, child_id, tree, labels, walker)
	gui.runScriptModalDialog(dlg, lambda result: _handle(result, dlg, on_commit))


def _handle(
	result: int, dlg: "_AssignDialog", on_commit: Callable[[ObjectId | None], None]
) -> None:
	if result == wx.ID_OK:
		on_commit(dlg.selected_parent_id)
	dlg.Destroy()


def _describe(oid: ObjectId, labels: LabelStore, walker: NVDAWalker) -> str:
	custom = labels.get(oid)
	if custom:
		return custom
	obj = walker.object_for_id(oid)
	if obj is not None:
		name = getattr(obj, "name", "") or ""
		role = getattr(obj, "roleText", "") or str(getattr(obj, "role", "") or "")
		text = f"{name} ({role})".strip()
		if text:
			return text
	return str(oid)


class _AssignDialog(wx.Dialog):
	def __init__(self, parent, child_id, tree, labels, walker):
		super().__init__(parent, title=_("Semantic Tree: assign"),
						 style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
		self._child_id = child_id
		self._tree = tree
		self._labels = labels
		self._walker = walker
		self._id_for_item: dict[wx.TreeItemId, ObjectId | None] = {}
		self._excluded = tree.explicit_descendants(child_id) | {child_id}

		sizer = wx.BoxSizer(wx.VERTICAL)
		sizer.Add(wx.StaticText(self, label=_("Choose a semantic parent:")), flag=wx.ALL, border=8)
		self._tree_ctrl = wx.TreeCtrl(self, style=wx.TR_HAS_BUTTONS | wx.TR_SINGLE | wx.TR_HIDE_ROOT)
		self._populate()
		sizer.Add(self._tree_ctrl, proportion=1, flag=wx.EXPAND | wx.ALL, border=8)
		btns = self.CreateButtonSizer(wx.OK | wx.CANCEL)
		sizer.Add(btns, flag=wx.EXPAND | wx.ALL, border=8)
		self.SetSizerAndFit(sizer)
		self.SetSize((500, 400))
		self._tree_ctrl.SetFocus()

	def _populate(self) -> None:
		root = self._tree_ctrl.AddRoot("")
		semantic_root = self._tree_ctrl.AppendItem(root, _("(top level)"))
		self._id_for_item[semantic_root] = None
		self._add_children(semantic_root, None)
		self._tree_ctrl.ExpandAllChildren(root)
		self._tree_ctrl.SelectItem(semantic_root)

	def _add_children(self, parent_item: wx.TreeItemId, parent_id: ObjectId | None) -> None:
		for cid in self._tree.explicit_children(parent_id):
			if cid in self._excluded:
				# Hide the object being assigned and its descendants to
				# prevent the user from picking a parent that would
				# create a cycle.
				continue
			item = self._tree_ctrl.AppendItem(parent_item, _describe(cid, self._labels, self._walker))
			self._id_for_item[item] = cid
			self._add_children(item, cid)

	@property
	def selected_parent_id(self) -> ObjectId | None:
		item = self._tree_ctrl.GetSelection()
		if not item.IsOk():
			return None
		return self._id_for_item.get(item)
