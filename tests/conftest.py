"""Test-time shims.

pyproject.toml already puts ``addon/globalPlugins`` and ``tests`` on
``sys.path`` via ``pythonpath``. We only need to define the ``_``
gettext builtin that NVDA normally provides at runtime.
"""

import builtins

if not hasattr(builtins, "_"):
	builtins._ = lambda s: s  # type: ignore[attr-defined]
