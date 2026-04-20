"""Stable identifiers for NVDA objects.

Goal: given the same on-screen element twice, produce the same hashable ID so
that semantic assignments and labels stay attached to it. The identity is a
tuple of attributes that together pin down one object on a running system.

The function accepts any object exposing these attributes (real NVDAObjects in
production, plain stub objects in tests), so the rest of the core never
imports NVDA itself.
"""

from collections.abc import Hashable
from typing import Any


def _attr(obj: Any, name: str, default: Any = "") -> Any:
	try:
		value = getattr(obj, name, default)
	except Exception:
		return default
	return default if value is None else value


def get_object_id(obj: Any) -> tuple[Hashable, ...] | None:
	"""Return a hashable identity tuple, or None if obj is None.

	The tuple mixes window identity (handle, control ID), semantic identity
	(role, name), and in-parent position. Any single field can drift (a name
	may change, a handle may be reused), but the composite is stable enough
	for a single session and for most cross-session reuse.
	"""
	if obj is None:
		return None
	return (
		str(_attr(obj, "appModuleName", "") or _attr(obj, "appName", "")),
		int(_attr(obj, "windowHandle", 0) or 0),
		int(_attr(obj, "windowControlID", 0) or 0),
		str(_attr(obj, "role", "")),
		str(_attr(obj, "name", "")),
		str(_attr(obj, "automationId", "")),
		int(_attr(obj, "indexInParent", -1) or -1),
	)
