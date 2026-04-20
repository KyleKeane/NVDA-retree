"""Fake NVDA-like objects plus a walker that uses real identity logic.

``FakeObject`` mirrors the bits of the NVDAObject surface area our code
actually touches: ``name``, ``role``, ``parent``, ``children``,
``windowHandle``, ``windowControlID``, ``appModule.appName``,
``indexInParent``, and ``UIAAutomationId``. ``FakeWalker`` delegates
``id_of`` to :func:`semanticTree.identity.get_object_id` so that the
tests exercise the same identity rule the production walker uses.
"""

from collections.abc import Iterable

from semanticTree.identity import get_object_id


class FakeAppModule:
	def __init__(self, app_name: str = "test") -> None:
		self.appName = app_name


class FakeObject:
	def __init__(
		self,
		name: str,
		role: str = "",
		children: list["FakeObject"] | None = None,
		app_name: str = "test",
		automation_id: str = "",
	) -> None:
		self.name = name
		self.role = role
		self.windowHandle = hash(name) & 0xFFFF
		self.windowControlID = 0
		self.appModule = FakeAppModule(app_name)
		self.UIAAutomationId = automation_id
		self.indexInParent = 0
		self.parent: FakeObject | None = None
		self._children: list[FakeObject] = []
		for child in children or []:
			self.add(child)

	def add(self, child: "FakeObject") -> "FakeObject":
		child.parent = self
		child.indexInParent = len(self._children)
		self._children.append(child)
		return child

	@property
	def children(self) -> list["FakeObject"]:
		return list(self._children)


class FakeWalker:
	def __init__(self) -> None:
		self._by_id: dict = {}

	def register(self, obj: FakeObject) -> None:
		oid = self.id_of(obj)
		if oid is not None:
			self._by_id[oid] = obj
		for child in obj.children:
			self.register(child)

	def remember(self, obj: FakeObject) -> None:
		oid = self.id_of(obj)
		if oid is not None:
			self._by_id.setdefault(oid, obj)

	def id_of(self, obj):
		return get_object_id(obj)

	def parent_of(self, obj):
		return obj.parent if obj else None

	def children_of(self, obj) -> Iterable[FakeObject]:
		return obj.children if obj else ()

	def object_for_id(self, oid):
		return self._by_id.get(oid)

	def forget(self, obj: FakeObject) -> None:
		"""Simulate a restart: drop an object from resolution but leave
		its identity discoverable via a live ancestor walk."""
		oid = self.id_of(obj)
		if oid is not None:
			self._by_id.pop(oid, None)

	def search_subtree(self, root: FakeObject, target_id, max_depth: int = 4, max_nodes: int = 500):
		"""BFS, used by the navigator's fallback path."""
		queue: list[tuple[FakeObject, int]] = [(root, 0)]
		visited = 0
		while queue and visited < max_nodes:
			obj, depth = queue.pop(0)
			visited += 1
			if self.id_of(obj) == target_id:
				self._by_id[target_id] = obj
				return obj
			if depth >= max_depth:
				continue
			for child in obj.children:
				queue.append((child, depth + 1))
		return None

	def prime_ancestors(self, obj: FakeObject, limit: int = 50) -> None:
		current = obj
		steps = 0
		while current is not None and steps < limit:
			oid = self.id_of(current)
			if oid is not None:
				self._by_id.setdefault(oid, current)
			current = current.parent
			steps += 1
