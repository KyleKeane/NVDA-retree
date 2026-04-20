"""Make the add-on's pure-Python modules importable without NVDA.

NVDA add-ons live under ``addon/globalPlugins/<name>/`` and use the
``_()`` gettext builtin. For tests we map the package to a plain import
path and define a no-op ``_``.
"""

import builtins
import os
import sys


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PKG_PATH = os.path.join(ROOT, "addon", "globalPlugins")
if PKG_PATH not in sys.path:
	sys.path.insert(0, PKG_PATH)

if not hasattr(builtins, "_"):
	builtins._ = lambda s: s  # type: ignore[attr-defined]
