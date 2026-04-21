"""Dialog: show the result of an update check; let the user install.

Entry point is :func:`run_update_check`. It runs the network call on
a background thread so NVDA's speech thread never blocks, then shows
a modal dialog back on the main thread with one of four messages:

* **up-to-date** — a single-button "Close" dialog.
* **update available** — includes the release notes and an Install
  button. Clicking Install downloads the ``.nvda-addon`` to a temp
  folder and hands it to NVDA's standard installer via
  :func:`updater.launch_install`.
* **no asset** — the release exists but ships no ``.nvda-addon``;
  shows a friendly explanation and a link to the release page.
* **error** — network failure, rate limit, or other; shows the
  exception message and a "Close" button.
"""

from __future__ import annotations

import threading
from collections.abc import Callable
from typing import Any

import gui  # type: ignore
import wx  # type: ignore

from .. import updater
from ..updater import CheckResult


REPO_OWNER = "KyleKeane"
REPO_NAME = "NVDA-retree"


def run_update_check(local_version: str) -> None:
	"""Kick off an update check. Shows a "checking" indicator, then
	a result dialog once the API call completes."""
	try:
		busy = wx.BusyInfo(_("Checking GitHub for Semantic Tree updates…"), parent=gui.mainFrame)
	except Exception:
		busy = None

	def worker() -> None:
		result = updater.check_for_update(REPO_OWNER, REPO_NAME, local_version)
		wx.CallAfter(_show_result, result, busy)

	threading.Thread(target=worker, daemon=True).start()


def _show_result(result: CheckResult, busy: Any) -> None:
	# Dismiss the "checking" indicator before the modal opens.
	try:
		del busy
	except Exception:
		pass
	if result.status == "up_to_date":
		_info(_("Semantic Tree is up to date."),
		      _("You are running version {current}. The latest release is {latest}.").format(
		          current=result.local_version, latest=result.remote_version))
	elif result.status == "update_available":
		_UpdateDialog(gui.mainFrame, result).ShowModal()
	elif result.status == "no_asset":
		_info(
			_("New version available but no download attached."),
			_(
				"Version {latest} was released but the GitHub release does not "
				"include a .nvda-addon file. Please visit {url} to investigate."
			).format(latest=result.remote_version, url=result.release_url or "GitHub"),
		)
	else:
		_info(
			_("Could not check for updates."),
			_(
				"The check failed: {error}\n\n"
				"Check your internet connection and try again."
			).format(error=result.error or _("unknown error")),
		)


def _info(title: str, message: str) -> None:
	try:
		gui.messageBox(message, caption=title, style=wx.OK | wx.ICON_INFORMATION)
	except Exception:
		# Fallback: announce through NVDA's speech if wx fails.
		try:
			import ui  # type: ignore
			ui.message(f"{title}. {message}")
		except Exception:
			pass


class _UpdateDialog(wx.Dialog):
	def __init__(self, parent, result: CheckResult) -> None:
		super().__init__(
			parent,
			title=_("Semantic Tree: update available"),
			style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
		)
		self._result = result

		sizer = wx.BoxSizer(wx.VERTICAL)
		summary = _(
			"A new version of the Semantic Tree add-on is available.\n\n"
			"Installed: {current}\nLatest:    {latest}\n"
		).format(current=result.local_version, latest=result.remote_version)
		sizer.Add(wx.StaticText(self, label=summary), flag=wx.ALL, border=8)

		if result.release_notes:
			sizer.Add(wx.StaticText(self, label=_("Release notes:")),
			          flag=wx.LEFT | wx.RIGHT, border=8)
			notes = wx.TextCtrl(
				self,
				value=result.release_notes,
				style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_DONTWRAP,
			)
			sizer.Add(notes, proportion=1, flag=wx.EXPAND | wx.ALL, border=8)

		buttons = wx.BoxSizer(wx.HORIZONTAL)
		install_button = wx.Button(self, label=_("&Install now"))
		install_button.Bind(wx.EVT_BUTTON, self._on_install)
		close_button = wx.Button(self, wx.ID_CANCEL, label=_("&Close"))
		buttons.Add(install_button, flag=wx.ALL, border=4)
		buttons.Add(close_button, flag=wx.ALL, border=4)
		sizer.Add(buttons, flag=wx.ALIGN_RIGHT)

		self.SetSizerAndFit(sizer)
		self.SetSize((560, 480))
		install_button.SetFocus()

	def _on_install(self, _event) -> None:
		# Keep the dialog visible until the download finishes so the
		# user sees the "downloading…" progression.
		self._set_buttons_enabled(False)
		threading.Thread(target=self._download_and_install, daemon=True).start()

	def _set_buttons_enabled(self, enabled: bool) -> None:
		for child in self.GetChildren():
			if isinstance(child, wx.Button):
				child.Enable(enabled)

	def _download_and_install(self) -> None:
		try:
			path = updater.download_addon(self._result.download_url)
		except Exception as exc:
			wx.CallAfter(self._finish_error, str(exc))
			return
		try:
			updater.launch_install(path)
		except Exception as exc:
			wx.CallAfter(self._finish_error, str(exc))
			return
		wx.CallAfter(self.EndModal, wx.ID_OK)

	def _finish_error(self, message: str) -> None:
		self._set_buttons_enabled(True)
		_info(_("Update failed"), message)
