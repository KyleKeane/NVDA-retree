"""Minimal test runner so contributors without pytest can still verify the
pure-Python core:

    python tests/run.py

For richer output install pytest and run ``pytest tests/``.
"""

import os
import sys
import traceback


def _setup_path():
	root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
	sys.path.insert(0, os.path.join(root, "addon", "globalPlugins"))
	sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
	sys.path.insert(0, root)
	import builtins
	if not hasattr(builtins, "_"):
		builtins._ = lambda s: s  # type: ignore[attr-defined]
	# Shim pytest if it isn't installed so the tests are still runnable.
	try:
		import pytest  # noqa: F401
	except ImportError:
		import types
		from contextlib import contextmanager
		stub = types.ModuleType("pytest")

		@contextmanager
		def raises(exc_type):
			try:
				yield
			except exc_type:
				return
			raise AssertionError(f"Did not raise {exc_type.__name__}")

		stub.raises = raises
		sys.modules["pytest"] = stub


def _collect():
	import test_identity
	import test_inheritance
	import test_labels
	import test_navigator
	import test_search
	import test_storage
	import test_tree

	modules = (
		test_tree,
		test_labels,
		test_inheritance,
		test_search,
		test_storage,
		test_identity,
		test_navigator,
	)
	cases = []
	for module in modules:
		for name in dir(module):
			if name.startswith("test_"):
				cases.append((f"{module.__name__}.{name}", getattr(module, name)))
	return cases


def _fake_tmp_path():
	import tempfile
	return tempfile.mkdtemp(prefix="semtree_")


def _run_one(name, fn):
	try:
		arg_names = fn.__code__.co_varnames[: fn.__code__.co_argcount]
		if "tmp_path" in arg_names:
			fn(_fake_tmp_path())
		else:
			fn()
	except Exception:
		print(f"FAIL  {name}")
		traceback.print_exc()
		return False
	print(f"ok    {name}")
	return True


def main() -> int:
	_setup_path()
	failed = 0
	for name, fn in _collect():
		if not _run_one(name, fn):
			failed += 1
	print()
	if failed:
		print(f"{failed} failure(s)")
		return 1
	print("all green")
	return 0


if __name__ == "__main__":
	sys.exit(main())
