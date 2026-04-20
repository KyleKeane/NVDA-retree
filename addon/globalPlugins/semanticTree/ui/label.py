"""Dialog: set or clear a custom label for the current navigator object."""

from collections.abc import Callable

import gui  # type: ignore
import wx  # type: ignore


def open_label_dialog(current: str, on_commit: Callable[[str], None]) -> None:
	dlg = _LabelDialog(gui.mainFrame, current)
	gui.runScriptModalDialog(dlg, lambda result: _handle(result, dlg, on_commit))


def _handle(result: int, dlg: "_LabelDialog", on_commit: Callable[[str], None]) -> None:
	if result == wx.ID_OK:
		on_commit(dlg.label.strip())
	dlg.Destroy()


class _LabelDialog(wx.Dialog):
	def __init__(self, parent, current: str):
		super().__init__(parent, title=_("Semantic Tree: label"))
		sizer = wx.BoxSizer(wx.VERTICAL)
		sizer.Add(wx.StaticText(self, label=_("Label (empty to clear):")), flag=wx.ALL, border=8)
		self._text = wx.TextCtrl(self, value=current or "")
		sizer.Add(self._text, flag=wx.EXPAND | wx.ALL, border=8)
		btns = self.CreateButtonSizer(wx.OK | wx.CANCEL)
		sizer.Add(btns, flag=wx.EXPAND | wx.ALL, border=8)
		self.SetSizerAndFit(sizer)
		self._text.SetFocus()

	@property
	def label(self) -> str:
		return self._text.GetValue()
