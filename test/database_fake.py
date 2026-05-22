"""In-memory Realtime Database stand-in for unit and e2e tests."""

from __future__ import annotations

from typing import Any


class _FakeReference:
    def __init__(self, store: dict[str, Any], path: str) -> None:
        self._store = store
        self._path = path

    def set(self, value: Any) -> None:
        self._store[self._path] = value

    def get(self) -> Any:
        return self._store.get(self._path)

    def delete(self) -> None:
        self._store.pop(self._path, None)


class InMemoryDatabase:
    """Minimal RTDB client that stores nodes in memory by path."""

    def __init__(self) -> None:
        self._store: dict[str, Any] = {}

    def reference(self, path: str) -> _FakeReference:
        return _FakeReference(self._store, path)

    def get_node(self, path: str) -> Any:
        return self._store.get(path)
