"""Test runner — stdlib only.

    python tests/run.py

Discovers every ``test_*.py`` in this directory, imports it, and runs
each top-level ``test_*`` function. A test passes if it does not raise.
Failures print their traceback and the runner exits non-zero.

Deliberately simple so it has no third-party dependencies. Good enough
for a project this size; when the test count grows past the point where
this is comfortable, migrate to ``unittest`` (also stdlib).
"""

import importlib.util
import os
import sys
import traceback


TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(TESTS_DIR)


def _setup_path() -> None:
	sys.path.insert(0, os.path.join(REPO_ROOT, "addon", "globalPlugins"))
	sys.path.insert(0, TESTS_DIR)
	sys.path.insert(0, REPO_ROOT)
	import builtins
	if not hasattr(builtins, "_"):
		builtins._ = lambda s: s  # type: ignore[attr-defined]


def _install_test_helpers() -> None:
	"""Expose a tiny ``testing_helpers`` module so tests can write
	``with raises(SomeError):`` without a third-party dependency."""
	import types
	from contextlib import contextmanager

	helpers = types.ModuleType("testing_helpers")

	@contextmanager
	def raises(exc_type):
		try:
			yield
		except exc_type:
			return
		raise AssertionError(f"Did not raise {exc_type.__name__}")

	helpers.raises = raises
	sys.modules["testing_helpers"] = helpers


def _discover_modules() -> list:
	names = sorted(
		f[:-3] for f in os.listdir(TESTS_DIR)
		if f.startswith("test_") and f.endswith(".py")
	)
	modules = []
	for name in names:
		spec = importlib.util.spec_from_file_location(name, os.path.join(TESTS_DIR, f"{name}.py"))
		if spec is None or spec.loader is None:
			continue
		module = importlib.util.module_from_spec(spec)
		sys.modules[name] = module
		spec.loader.exec_module(module)
		modules.append(module)
	return modules


def _collect() -> list:
	cases = []
	for module in _discover_modules():
		for name in sorted(dir(module)):
			if not name.startswith("test_"):
				continue
			fn = getattr(module, name)
			if callable(fn):
				cases.append((f"{module.__name__}.{name}", fn))
	return cases


def _run_one(case_name: str, fn) -> bool:
	try:
		fn()
	except Exception:
		print(f"FAIL  {case_name}")
		traceback.print_exc()
		return False
	print(f"ok    {case_name}")
	return True


def main() -> int:
	_setup_path()
	_install_test_helpers()
	failed = 0
	total = 0
	for case_name, fn in _collect():
		total += 1
		if not _run_one(case_name, fn):
			failed += 1
	print()
	if failed:
		print(f"{failed} of {total} failed")
		return 1
	print(f"all {total} green")
	return 0


if __name__ == "__main__":
	sys.exit(main())
