from __future__ import annotations

from collections import OrderedDict
from typing import (
    Any,
    Callable,
    Generic,
    Hashable,
    Iterable,
    Iterator,
    Optional,
    TypeVar,
)

T = TypeVar("T", bound="Hashable")


class OrderedSet(Generic[T]):
    __slots__ = ("_items",)

    def __init__(self) -> None:
        self._items: OrderedDict[T, None] = OrderedDict()

    @classmethod
    def from_iter(cls, items: Iterable[T]) -> OrderedSet[T]:
        container = cls()
        for item in items:
            container.add(item)
        return container

    def sorted(self, *, key: Optional[Callable[[T], Any]] = None) -> OrderedSet[T]:
        items = list(self)
        items.sort(key=key)
        return type(self).from_iter(items)

    def add(self, item: T) -> None:
        self._items[item] = None

    def extend(self, other: OrderedSet[T]) -> None:
        self._items.update(other._items)

    def remove(self, item: T) -> None:
        del self._items[item]

    def __contains__(self, item: T) -> bool:
        return item in self._items

    def __delitem__(self, item: T) -> None:
        del self._items[item]

    def __iter__(self) -> Iterator[T]:
        return iter(self._items)

    def __and__(self, other: OrderedSet[T]) -> OrderedSet[T]:
        intersection = self._items.keys() & other._items.keys()
        return self.from_iter(intersection)

    def __len__(self) -> int:
        return len(self._items)

    def __str__(self) -> str:
        return str(set(self))
