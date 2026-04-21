"""Dialog: set or clear a custom label for the current navigator object."""

from collections.abc import Callable

import gui  # type: ignore
import wx  # type: ignore


def open_label_dialog(
	current: str,
	on_commit: Callable[[str, bool], None],
) -> None:
	"""Open the label dialog.

	``on_commit`` is called with ``(label_text, ignore_name)`` where
	``ignore_name`` reflects whether the user ticked the wildcard
	checkbox (so the plugin can choose between storing an exact ID
	or a name-agnostic pattern).
	"""
	try:
		dlg = _LabelDialog(gui.mainFrame, current)
		gui.runScriptModalDialog(dlg, lambda result: _handle(result, dlg, on_commit))
	except Exception as exc:
		_report_dialog_failure(exc)


def _report_dialog_failure(exc: Exception) -> None:
	try:
		import ui  # type: ignore
		ui.message(_("Could not open dialog: {}").format(exc))
	except Exception:
		pass


def _handle(
	result: int,
	dlg: "_LabelDialog",
	on_commit: Callable[[str, bool], None],
) -> None:
	if result == wx.ID_OK:
		on_commit(dlg.label.strip(), dlg.ignore_name)
	dlg.Destroy()


class _LabelDialog(wx.Dialog):
	def __init__(self, parent, current: str):
		super().__init__(parent, title=_("Semantic Tree: label"))
		sizer = wx.BoxSizer(wx.VERTICAL)
		sizer.Add(
			wx.StaticText(self, label=_("Label (empty to clear):")),
			flag=wx.ALL, border=8,
		)
		self._text = wx.TextCtrl(self, value=current or "")
		sizer.Add(self._text, flag=wx.EXPAND | wx.ALL, border=8)

		self._ignore_name = wx.CheckBox(
			self,
			label=_(
				"&Apply this label to any object with the same role and "
				"position (ignore name changes)"
			),
		)
		sizer.Add(self._ignore_name, flag=wx.LEFT | wx.RIGHT | wx.BOTTOM, border=8)

		btns = self.CreateButtonSizer(wx.OK | wx.CANCEL)
		sizer.Add(btns, flag=wx.EXPAND | wx.ALL, border=8)
		self.SetSizerAndFit(sizer)
		self._text.SetFocus()

	@property
	def label(self) -> str:
		return self._text.GetValue()

	@property
	def ignore_name(self) -> bool:
		return bool(self._ignore_name.GetValue())
