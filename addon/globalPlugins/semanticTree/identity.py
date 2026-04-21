"""Stable identifiers for NVDA objects, scoped by app and path.

Goal: given the same on-screen element across sessions — close the
app, reopen it, NVDA restart, tomorrow — produce the same hashable
ID so the user's semantic-tree assignments and labels stay attached
to it.

Shape
-----
::

    ObjectId = (
        app_name: str,                   # obj.appModule.appName
        path: tuple[NodeSignature, ...]  # root-to-self, one per ancestor
    )

    NodeSignature = (
        role: str,                       # obj.role
        discriminator: str,              # most stable identifier we can find
        sibling_index: int,              # nth sibling sharing (role, discriminator)
    )

Nothing OS-assigned (no ``windowHandle``, no ``windowControlID``)
appears anywhere, so the ID survives every Windows re-launch.

Discriminator policy (per node)
-------------------------------
We pick the most stable of three candidates, preferring the first
that produces a non-empty, non-garbage value:

1. ``UIAAutomationId`` / ``automationId`` if it looks stable
   (non-empty, not all-digits, not GUID-shaped, not absurdly long).
   WPF, Electron and some web surfaces auto-generate IDs that fail
   this check and fall through.
2. ``windowClassName``. Stable for every Win32-backed object
   (main windows: ``"Notepad"``, ``"MozillaWindowClass"``;
   inner controls: ``"Edit"``, ``"Button"``). Also the stable
   choice for the root (app main window) where ``name`` is a
   dynamic document title.
3. ``name``. Fallback for pure UIA/HTML surfaces without a
   ``windowClassName``.

``sibling_index`` disambiguates within siblings that share the same
``(role, discriminator)`` — e.g. three unlabelled ``listItem``s
become ``sibling_index`` 0, 1, 2 under the same parent.

The rest of the code treats ``ObjectId`` as opaque. If you improve
identity later (e.g. pattern-matching with wildcards), make the
change in this module only.
"""

from collections.abc import Hashable
from typing import Any


_MISSING = object()
_MAX_PATH_DEPTH = 64
_MAX_AUTO_ID_LEN = 128


def _get(obj: Any, path: str) -> Any:
	"""Return ``obj.part1.part2...`` or ``_MISSING`` on any failure."""
	current: Any = obj
	for part in path.split("."):
		try:
			current = getattr(current, part, _MISSING)
		except Exception:
			return _MISSING
		if current is _MISSING or current is None:
			return _MISSING
	return current


def _str_of(obj: Any, *paths: str) -> str:
	for path in paths:
		value = _get(obj, path)
		if value is _MISSING:
			continue
		text = str(value)
		if text:
			return text
	return ""


def _is_stable_automation_id(text: str) -> bool:
	"""Heuristic: does this look like a hand-chosen identifier or an
	auto-generated one that differs per launch?"""
	if not text or len(text) > _MAX_AUTO_ID_LEN:
		return False
	if text.isdigit():
		# e.g. "47", "12345" — often an autogen index.
		return False
	if len(text) >= 32 and all(c in "0123456789abcdef-" for c in text.lower()):
		# GUID-shape.
		return False
	return True


def _discriminator(obj: Any) -> str:
	"""Most stable single-string identifier available on ``obj``.

	Applied per node. Independent of position — ``sibling_index``
	handles ambiguity within siblings.
	"""
	auto_id = _str_of(obj, "UIAAutomationId", "automationId")
	if _is_stable_automation_id(auto_id):
		return auto_id
	class_name = _str_of(obj, "windowClassName")
	if class_name:
		return class_name
	return _str_of(obj, "name")


def _sibling_index(obj: Any, role: str, discriminator: str) -> int:
	"""Return the 0-based position of ``obj`` among its parent's
	children that share the same ``(role, discriminator)``.

	Returns 0 if obj has no parent or is not found among its parent's
	children (defensive — shouldn't happen with well-formed trees).
	"""
	parent = _get(obj, "parent")
	if parent is _MISSING:
		return 0
	children = _get(parent, "children")
	if children is _MISSING:
		return 0
	count = 0
	for sibling in children:
		if sibling is obj:
			return count
		if _str_of(sibling, "role") == role and _discriminator(sibling) == discriminator:
			count += 1
	return count


def _node_signature(obj: Any) -> tuple:
	role = _str_of(obj, "role")
	discriminator = _discriminator(obj)
	index = _sibling_index(obj, role, discriminator)
	return (role, discriminator, index)


def _path_signature(obj: Any) -> tuple:
	"""Walk from ``obj`` up to the topmost reachable ancestor and
	return their signatures, root-first."""
	nodes = []
	current = obj
	depth = 0
	while current is not None and depth < _MAX_PATH_DEPTH:
		nodes.append(_node_signature(current))
		parent = _get(current, "parent")
		if parent is _MISSING:
			break
		current = parent
		depth += 1
	nodes.reverse()
	return tuple(nodes)


def get_object_id(obj: Any) -> tuple[Hashable, ...] | None:
	"""Return a hashable identity for ``obj`` or ``None`` if ``obj`` is ``None``."""
	if obj is None:
		return None
	return (
		_str_of(obj, "appModule.appName", "appName"),
		_path_signature(obj),
	)
