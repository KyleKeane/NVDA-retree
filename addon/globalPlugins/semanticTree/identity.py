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


_MISSING = object()


def _get(obj: Any, path: str) -> Any:
	"""Return ``obj.part1.part2...`` or ``_MISSING`` on any failure.

	NVDA spreads its identity bits across several objects (for example
	``obj.appModule.appName``), so we walk dotted attribute paths
	instead of a flat ``getattr``.
	"""
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
	"""First non-empty dotted attribute value along ``paths``, as a string."""
	for path in paths:
		value = _get(obj, path)
		if value is _MISSING:
			continue
		text = str(value)
		if text:
			return text
	return ""


def _int_of(obj: Any, path: str, default: int = 0) -> int:
	"""Dotted attribute value as an int, preserving 0 and negative values."""
	value = _get(obj, path)
	if value is _MISSING:
		return default
	try:
		return int(value)
	except (TypeError, ValueError):
		return default


def get_object_id(obj: Any) -> tuple[Hashable, ...] | None:
	"""Return a hashable identity tuple, or ``None`` if ``obj`` is ``None``.

	The tuple mixes window identity (handle, control ID), semantic
	identity (role, name), and in-parent position. Any single field can
	drift (a name may change, a handle may be reused), but the composite
	is stable enough for a single session and for most cross-session
	reuse. If you improve identity later (e.g. by preferring UIA
	``runtimeId`` when available), make the change here only — the rest
	of the code treats ``ObjectId`` as opaque.
	"""
	if obj is None:
		return None
	return (
		_str_of(obj, "appModule.appName", "appName"),
		_int_of(obj, "windowHandle"),
		_int_of(obj, "windowControlID"),
		_str_of(obj, "role"),
		_str_of(obj, "name"),
		_str_of(obj, "UIAAutomationId", "automationId"),
		_int_of(obj, "indexInParent", default=-1),
	)
