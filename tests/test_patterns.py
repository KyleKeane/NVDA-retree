"""Tests for the pattern-matching engine."""

from semanticTree import patterns
from semanticTree.patterns import WILDCARD


def _id(app, *nodes):
	return (app, tuple(nodes))


# ---------- matches ----------


def test_matches_exact_equality():
	oid = _id("firefox", ("window", "MozillaWindowClass", 0), ("button", "Reload", 2))
	assert patterns.matches(oid, oid) is True


def test_wildcard_discriminator_matches_any_name():
	stored = _id("firefox", ("window", "MozillaWindowClass", 0), ("button", WILDCARD, 2))
	live = _id("firefox", ("window", "MozillaWindowClass", 0), ("button", "Reload", 2))
	assert patterns.matches(stored, live) is True


def test_wildcard_sibling_index_matches_any_position():
	stored = _id("firefox", ("window", "MozillaWindowClass", 0), ("button", "Reload", WILDCARD))
	live = _id("firefox", ("window", "MozillaWindowClass", 0), ("button", "Reload", 7))
	assert patterns.matches(stored, live) is True


def test_role_difference_never_matches():
	stored = _id("firefox", ("button", WILDCARD, WILDCARD))
	live = _id("firefox", ("link", "Reload", 2))
	assert patterns.matches(stored, live) is False


def test_app_difference_never_matches():
	stored = _id("firefox", ("button", WILDCARD, WILDCARD))
	live = _id("chrome", ("button", "Reload", 2))
	assert patterns.matches(stored, live) is False


def test_path_length_mismatch_is_never_a_match():
	stored = _id("firefox", ("window", "MozillaWindowClass", 0))
	live = _id("firefox", ("window", "MozillaWindowClass", 0), ("button", "Reload", 2))
	assert patterns.matches(stored, live) is False


def test_concrete_stored_value_differing_from_live_does_not_match():
	stored = _id("firefox", ("button", "Save", 0))
	live = _id("firefox", ("button", "Reload", 0))
	assert patterns.matches(stored, live) is False


# ---------- is_pattern ----------


def test_is_pattern_false_for_exact_id():
	assert patterns.is_pattern(_id("firefox", ("button", "Reload", 2))) is False


def test_is_pattern_true_when_discriminator_is_wildcard():
	assert patterns.is_pattern(_id("firefox", ("button", WILDCARD, 2))) is True


def test_is_pattern_true_when_sibling_index_is_wildcard():
	assert patterns.is_pattern(_id("firefox", ("button", "Reload", WILDCARD))) is True


def test_is_pattern_false_on_non_id_inputs():
	assert patterns.is_pattern(None) is False
	assert patterns.is_pattern("hello") is False
	assert patterns.is_pattern(42) is False


# ---------- specificity ----------


def test_specificity_counts_concrete_slots():
	exact = _id("firefox", ("button", "Reload", 2))
	one_wild = _id("firefox", ("button", WILDCARD, 2))
	two_wild = _id("firefox", ("button", WILDCARD, WILDCARD))
	assert patterns.specificity(exact) > patterns.specificity(one_wild)
	assert patterns.specificity(one_wild) > patterns.specificity(two_wild)


# ---------- name_agnostic ----------


def test_name_agnostic_wildcards_only_the_leaf_discriminator():
	oid = _id("firefox", ("window", "MozillaWindowClass", 0), ("button", "Save", 3))
	out = patterns.name_agnostic(oid)
	# App name preserved.
	assert out[0] == "firefox"
	# Ancestor node untouched.
	assert out[1][0] == ("window", "MozillaWindowClass", 0)
	# Leaf: role and index preserved, discriminator nulled.
	assert out[1][-1] == ("button", WILDCARD, 3)


def test_name_agnostic_preserves_role_and_sibling_index():
	oid = _id("app", ("edit", "Edit", 7))
	out = patterns.name_agnostic(oid)
	role, disc, idx = out[1][-1]
	assert role == "edit"
	assert disc is WILDCARD
	assert idx == 7


def test_name_agnostic_yields_matches_for_renamed_sibling():
	stored = patterns.name_agnostic(
		_id("firefox", ("window", "MozillaWindowClass", 0), ("button", "Save", 3))
	)
	live_after_rename = _id(
		"firefox", ("window", "MozillaWindowClass", 0), ("button", "Save As…", 3),
	)
	assert patterns.matches(stored, live_after_rename) is True


def test_name_agnostic_handles_empty_path_gracefully():
	oid = ("app", ())
	assert patterns.name_agnostic(oid) == oid
