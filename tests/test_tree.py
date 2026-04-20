from testing_helpers import raises

from semanticTree.tree import CycleError, SemanticTree


def test_assign_and_parent_of():
	t = SemanticTree()
	t.assign("a", None)
	t.assign("b", "a")
	assert t.parent_of("b") == "a"
	assert t.parent_of("a") is None
	assert t.is_assigned("b")


def test_unassign():
	t = SemanticTree()
	t.assign("a", None)
	t.unassign("a")
	assert not t.is_assigned("a")


def test_explicit_children_ordering():
	t = SemanticTree()
	t.assign("p", None)
	t.assign("x", "p")
	t.assign("y", "p")
	assert set(t.explicit_children("p")) == {"x", "y"}


def test_cycle_detection():
	t = SemanticTree()
	t.assign("a", None)
	t.assign("b", "a")
	with raises(CycleError):
		t.assign("a", "b")


def test_self_cycle():
	t = SemanticTree()
	with raises(CycleError):
		t.assign("a", "a")


def test_explicit_descendants():
	t = SemanticTree()
	t.assign("root", None)
	t.assign("child1", "root")
	t.assign("child2", "root")
	t.assign("grandchild", "child1")
	assert t.explicit_descendants("root") == {"child1", "child2", "grandchild"}
	assert t.explicit_descendants("child1") == {"grandchild"}
	assert t.explicit_descendants("grandchild") == set()


def test_round_trip_serialisation():
	t = SemanticTree()
	t.assign(("app", 1, "root", ""), None)
	t.assign(("app", 1, "child", ""), ("app", 1, "root", ""))
	restored = SemanticTree.from_dict(t.to_dict())
	assert list(restored.assigned_ids()) == list(t.assigned_ids())
	for oid in t.assigned_ids():
		assert restored.parent_of(oid) == t.parent_of(oid)
