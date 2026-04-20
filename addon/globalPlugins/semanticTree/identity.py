"""Stable identifiers for NVDA objects.

Goal: given the same on-screen element twice, produce the same hashable ID so
that semantic assignments and labels stay attached to it. The identity is a
tuple of attributes that together pin down one object on a running system.

The function accepts any object exposing these attributes (real NVDAObjects
in production, plain stub objects in tests), so the rest of the core never
imports NVDA itself.
"""

from collections.abc import Hashable
from typing import Any


_SENTINEL = object()


def _get(obj: Any, path: str, default: Any = "") -> Any:
	"""Return ``obj.part1.part2...`` or ``default`` on any failure.

	NVDA spreads its identity bits across several objects (for example
	``obj.appModule.appName``), so we walk dotted attribute paths instead
	of a flat ``getattr``.
	"""
	current: Any = obj
	for part in path.split("."):
		try:
			current = getattr(current, part, _SENTINEL)
		except Exception:
			return default
		if current is _SENTINEL or current is None:
			return default
	return current


def get_object_id(obj: Any) -> tuple[Hashable, ...] | None:
	"""Return a hashable identity tuple, or ``None`` if obj is ``None``.

	The tuple mixes window identity (handle, control ID), semantic
	identity (role, name), and in-parent position. Any single field can
	drift (a name may change, a handle may be reused), but the composite
	is stable enough for a single session and for most cross-session
	reuse. If you improve identity later (e.g. by using UIA
	``runtimeId`` when available), make the change here only — the rest
	of the code treats ``ObjectId`` as opaque.
	"""
	if obj is None:
		return None
	return (
		str(_get(obj, "appModule.appName") or _get(obj, "appName") or ""),
		int(_get(obj, "windowHandle", 0) or 0),
		int(_get(obj, "windowControlID", 0) or 0),
		str(_get(obj, "role", "")),
		str(_get(obj, "name", "")),
		str(_get(obj, "UIAAutomationId") or _get(obj, "automationId") or ""),
		int(_get(obj, "indexInParent", -1) or -1),
	)
