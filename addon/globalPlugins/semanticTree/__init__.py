"""Semantic Tree add-on package.

Importing this package is safe without NVDA (tests rely on that). The
NVDA global-plugin entry point lives in :mod:`plugin` and is only pulled
in when NVDA's core modules are importable.
"""

try:
	import globalPluginHandler  # noqa: F401

	from .plugin import GlobalPlugin  # noqa: F401
except ImportError:
	# Running outside NVDA (e.g. unit tests). The core modules
	# (tree, inheritance, labels, storage, search) are fully usable.
	pass
