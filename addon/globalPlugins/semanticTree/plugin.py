"""Semantic Tree global plugin.

Entry point that NVDA loads. Responsibilities:
  * Load the saved semantic tree and label store from disk.
  * Register the four navigation gestures, the label gesture, the assign
    gesture, and the search gesture.
  * Route each gesture to the navigator or to a UI dialog.

The core logic is deliberately kept out of this file so that you can read
it top-to-bottom and see what every shortcut does.
"""

import os

import api  # type: ignore
import globalPluginHandler  # type: ignore
import globalVars  # type: ignore
import ui  # type: ignore
from scriptHandler import script  # type: ignore

from . import storage
from .labels import LabelStore
from .navigator import SemanticNavigator, sync_nvda_navigator
from .walker import NVDAWalker


def _data_path() -> str:
	config_dir = getattr(getattr(globalVars, "appArgs", None), "configPath", None)
	if not config_dir:
		config_dir = os.path.expanduser("~/.nvda")
	return os.path.join(config_dir, "semanticTree.json")


def _installed_version() -> str:
	"""Read this add-on's installed version from NVDA's registered
	add-on metadata. Falls back to reading ``manifest.ini`` directly
	if the NVDA API call fails (e.g. during development via the
	scratchpad, where there is no installed add-on record)."""
	try:
		import addonHandler  # type: ignore
		for addon in addonHandler.getAvailableAddons():
			if getattr(addon, "name", "") == "semanticTree":
				manifest = getattr(addon, "manifest", {}) or {}
				version = manifest.get("version")
				if version:
					return str(version)
	except Exception:
		pass
	# Scratchpad / unit-test fallback: read the shipped manifest.
	manifest_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
		os.path.abspath(__file__)))), "manifest.ini")
	try:
		with open(manifest_path, encoding="utf-8") as f:
			for line in f:
				stripped = line.strip()
				if stripped.startswith("version"):
					_, _, value = stripped.partition("=")
					return value.strip().strip('"').strip("'")
	except Exception:
		pass
	return "0.0.0"


def _role_text(obj) -> str:
	"""Human-readable role name, tolerant of NVDA API drift.

	Tries, in order:
	  1. ``obj.roleText`` (some drivers pre-compute this).
	  2. ``role.displayString`` (modern NVDA: controlTypes.Role enum).
	  3. ``controlTypes.roleLabels[role]`` (legacy NVDA dict).
	  4. ``str(role)`` as a last resort.
	"""
	pre = getattr(obj, "roleText", None)
	if pre:
		return str(pre)
	role = getattr(obj, "role", None)
	if role is None:
		return ""
	display = getattr(role, "displayString", None)
	if display:
		return str(display)
	try:
		import controlTypes  # type: ignore
	except ImportError:
		return str(role)
	role_labels = getattr(controlTypes, "roleLabels", None)
	if role_labels is not None:
		try:
			text = role_labels.get(role) if hasattr(role_labels, "get") else role_labels[role]
		except (KeyError, TypeError):
			text = None
		if text:
			return str(text)
	return str(role)


def describe(obj, labels: LabelStore, walker: NVDAWalker) -> str:
	if obj is None:
		return _("nothing")
	oid = walker.id_of(obj)
	custom = labels.get(oid) if oid is not None else None
	if custom:
		return custom
	name = getattr(obj, "name", None) or ""
	role = _role_text(obj)
	text = f"{name} {role}".strip()
	return text or _("unnamed object")


class GlobalPlugin(globalPluginHandler.GlobalPlugin):
	scriptCategory = _("Semantic Tree")

	def __init__(self) -> None:
		super().__init__()
		self._path = _data_path()
		self._tree, self._labels = storage.load(self._path)
		self._walker = NVDAWalker()
		self._nav = SemanticNavigator(self._tree, self._walker)
		self._update_menu_item = None
		self._register_tools_menu_item()

	def _register_tools_menu_item(self) -> None:
		"""Add 'Check for Semantic Tree updates…' under NVDA → Tools.

		All of this is wrapped in try/except because the exact shape of
		``gui.mainFrame.sysTrayIcon.toolsMenu`` has varied across NVDA
		versions; a failure here should not prevent the add-on from
		loading."""
		try:
			import wx  # type: ignore
			import gui  # type: ignore
			tools_menu = gui.mainFrame.sysTrayIcon.toolsMenu
			self._update_menu_item = tools_menu.Append(
				wx.ID_ANY,
				_("Check for Semantic Tree &updates…"),
				_("Ask GitHub whether a newer version of the Semantic Tree add-on is available."),
			)
			gui.mainFrame.sysTrayIcon.Bind(
				wx.EVT_MENU,
				self._on_check_for_updates,
				self._update_menu_item,
			)
		except Exception:
			self._update_menu_item = None

	def _unregister_tools_menu_item(self) -> None:
		if self._update_menu_item is None:
			return
		try:
			import gui  # type: ignore
			gui.mainFrame.sysTrayIcon.toolsMenu.Remove(self._update_menu_item)
		except Exception:
			pass
		self._update_menu_item = None

	def _on_check_for_updates(self, _event) -> None:
		from .ui.update import run_update_check
		run_update_check(_installed_version())

	def terminate(self) -> None:
		self._unregister_tools_menu_item()
		try:
			storage.save(self._path, self._tree, self._labels)
		finally:
			super().terminate()

	def _announce(self, obj) -> None:
		ui.message(describe(obj, self._labels, self._walker))
		sync_nvda_navigator(obj)

	def _current_navigator(self):
		try:
			return api.getNavigatorObject()
		except Exception:
			return None

	def _anchor_to_navigator(self) -> bool:
		"""Re-sync the semantic cursor to NVDA's current navigator on every
		press. Essential: the user may have moved NVDA's navigator via
		other gestures in between ours, and we want semantic moves to
		always start from where the user actually is."""
		obj = self._current_navigator()
		if obj is None:
			ui.message(_("No navigator object"))
			return False
		if self._nav.current is not obj:
			self._nav.focus(obj)
			# Prime the walker cache with the ancestor chain so up-moves
			# and sibling moves can resolve IDs even before we've
			# traversed them.
			self._walker.prime_ancestors(obj)
		return True

	@script(
		description=_("Move to the semantic parent of the current navigator object."),
		gesture="kb:NVDA+control+shift+upArrow",
	)
	def script_semantic_parent(self, gesture) -> None:
		if not self._anchor_to_navigator():
			return
		new_obj = self._nav.to_parent()
		if new_obj is None:
			ui.message(_("No semantic parent"))
			return
		self._announce(new_obj)

	@script(
		description=_("Move to the first semantic child of the current navigator object."),
		gesture="kb:NVDA+control+shift+downArrow",
	)
	def script_semantic_first_child(self, gesture) -> None:
		if not self._anchor_to_navigator():
			return
		new_obj = self._nav.to_first_child()
		if new_obj is None:
			ui.message(_("No semantic children"))
			return
		self._announce(new_obj)

	@script(
		description=_("Move to the previous semantic sibling."),
		gesture="kb:NVDA+control+shift+leftArrow",
	)
	def script_semantic_previous(self, gesture) -> None:
		if not self._anchor_to_navigator():
			return
		new_obj = self._nav.to_previous_sibling()
		if new_obj is None:
			ui.message(_("No previous semantic sibling"))
			return
		self._announce(new_obj)

	@script(
		description=_("Move to the next semantic sibling."),
		gesture="kb:NVDA+control+shift+rightArrow",
	)
	def script_semantic_next(self, gesture) -> None:
		if not self._anchor_to_navigator():
			return
		new_obj = self._nav.to_next_sibling()
		if new_obj is None:
			ui.message(_("No next semantic sibling"))
			return
		self._announce(new_obj)

	@script(
		description=_("Set a custom label for the current navigator object."),
		gesture="kb:NVDA+control+shift+l",
	)
	def script_set_label(self, gesture) -> None:
		from .ui.label import open_label_dialog
		obj = self._current_navigator()
		if obj is None:
			ui.message(_("No navigator object"))
			return
		oid = self._walker.id_of(obj)
		if oid is None:
			ui.message(_("Cannot label this object"))
			return
		current = self._labels.get(oid) or ""
		open_label_dialog(current, lambda text: self._commit_label(oid, text))

	def _commit_label(self, oid, text: str) -> None:
		self._labels.set(oid, text)
		storage.save(self._path, self._tree, self._labels)
		ui.message(_("Label saved") if text else _("Label cleared"))

	@script(
		description=_("Assign the current navigator object to a position in the semantic tree."),
		gesture="kb:NVDA+control+shift+a",
	)
	def script_assign(self, gesture) -> None:
		from .ui.assign import open_assign_dialog
		obj = self._current_navigator()
		if obj is None:
			ui.message(_("No navigator object"))
			return
		oid = self._walker.id_of(obj)
		if oid is None:
			ui.message(_("Cannot assign this object"))
			return
		self._walker.remember(obj)
		self._walker.prime_ancestors(obj)
		open_assign_dialog(
			child_id=oid,
			tree=self._tree,
			labels=self._labels,
			walker=self._walker,
			on_commit=lambda parent_id: self._commit_assignment(oid, parent_id),
		)

	def _commit_assignment(self, child_id, parent_id) -> None:
		try:
			self._tree.assign(child_id, parent_id)
		except Exception as exc:
			ui.message(_("Assignment failed: {}").format(exc))
			return
		storage.save(self._path, self._tree, self._labels)
		ui.message(_("Assigned"))

	@script(
		description=_("Search the semantic tree by label, role, or path."),
		gesture="kb:NVDA+control+shift+f",
	)
	def script_search(self, gesture) -> None:
		from .ui.search import open_search_dialog
		anchor = self._current_navigator()
		if anchor is not None:
			self._walker.prime_ancestors(anchor)
		open_search_dialog(
			tree=self._tree,
			labels=self._labels,
			walker=self._walker,
			on_pick=self._go_to,
		)

	def _go_to(self, obj) -> None:
		if obj is None:
			return
		self._nav.focus(obj)
		self._announce(obj)
