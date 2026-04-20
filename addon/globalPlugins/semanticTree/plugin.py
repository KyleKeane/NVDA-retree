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

import globalPluginHandler  # type: ignore
import globalVars  # type: ignore
import ui  # type: ignore
import api  # type: ignore
from scriptHandler import script  # type: ignore

from . import storage
from .labels import LabelStore
from .navigator import SemanticNavigator, sync_nvda_navigator
from .tree import SemanticTree
from .walker import NVDAWalker


def _data_path() -> str:
	base = getattr(globalVars, "appArgs", None)
	config_dir = getattr(base, "configPath", None) if base else None
	if not config_dir:
		config_dir = os.path.expanduser("~/.nvda")
	return os.path.join(config_dir, "semanticTree.json")


def describe(obj, labels: LabelStore, walker: NVDAWalker) -> str:
	if obj is None:
		return _("nothing")
	oid = walker.id_of(obj)
	custom = labels.get(oid) if oid is not None else None
	if custom:
		return custom
	name = getattr(obj, "name", None) or ""
	role = getattr(obj, "roleText", None) or str(getattr(obj, "role", "") or "")
	return f"{name} {role}".strip() or _("unnamed object")


class GlobalPlugin(globalPluginHandler.GlobalPlugin):
	scriptCategory = _("Semantic Tree")

	def __init__(self) -> None:
		super().__init__()
		self._path = _data_path()
		self._tree, self._labels = storage.load(self._path)
		self._walker = NVDAWalker()
		self._nav = SemanticNavigator(self._tree, self._walker)

	def terminate(self) -> None:
		try:
			storage.save(self._path, self._tree, self._labels)
		finally:
			super().terminate()

	def _announce(self, obj) -> None:
		ui.message(describe(obj, self._labels, self._walker))
		sync_nvda_navigator(obj)

	def _anchor_to_navigator(self) -> None:
		if self._nav.current is None:
			self._nav.focus(api.getNavigatorObject())

	@script(
		description=_("Move to the semantic parent of the current navigator object."),
		gesture="kb:NVDA+control+shift+upArrow",
	)
	def script_semantic_parent(self, gesture) -> None:
		self._anchor_to_navigator()
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
		self._anchor_to_navigator()
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
		self._anchor_to_navigator()
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
		self._anchor_to_navigator()
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
		obj = api.getNavigatorObject()
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
		obj = api.getNavigatorObject()
		oid = self._walker.id_of(obj)
		if oid is None:
			ui.message(_("Cannot assign this object"))
			return
		self._walker.remember(obj)
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
