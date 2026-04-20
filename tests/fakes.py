"""Fake NVDA-like objects + a walker for driving core logic in tests."""

from typing import Iterable, List, Optional


class FakeObject:
	def __init__(self, name: str, role: str = "", children: Optional[List["FakeObject"]] = None):
		self.name = name
		self.role = role
		self.windowHandle = hash(name) & 0xFFFF
		self.windowControlID = 0
		self.appModuleName = "test"
		self.automationId = ""
		self.indexInParent = 0
		self.parent: Optional[FakeObject] = None
		self._children: List[FakeObject] = []
		for child in children or []:
			self.add(child)

	def add(self, child: "FakeObject") -> "FakeObject":
		child.parent = self
		child.indexInParent = len(self._children)
		self._children.append(child)
		return child

	@property
	def children(self) -> List["FakeObject"]:
		return list(self._children)


class FakeWalker:
	def __init__(self):
		self._by_id = {}

	def register(self, obj: FakeObject) -> None:
		self._by_id[self.id_of(obj)] = obj
		for child in obj.children:
			self.register(child)

	def id_of(self, obj) -> Optional[tuple]:
		if obj is None:
			return None
		return (obj.appModuleName, obj.windowHandle, obj.name, obj.role)

	def parent_of(self, obj):
		return obj.parent if obj else None

	def children_of(self, obj) -> Iterable[FakeObject]:
		return obj.children if obj else ()

	def object_for_id(self, oid):
		return self._by_id.get(oid)
