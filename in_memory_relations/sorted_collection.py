from bisect import insort
from typing import Generic, Hashable, Iterator, List, Optional, Protocol, Set, TypeVar

T = TypeVar("T", bound="Comparable")


class Comparable(Hashable, Protocol):
    def __lt__(self: T, other: T) -> bool:
        pass


class SortedCollection(Generic[T]):
    def __init__(self) -> None:
        self._items_list: List[T] = list()
        self._items_set: Set[T] = set()

    def __len__(self) -> int:
        return len(self._items_list)

    def add(self, item: T) -> None:
        if item not in self._items_set:
            insort(self._items_list, item)
            self._items_set.add(item)

    def remove(self, item: T) -> None:
        if item in self._items_set:
            index = bisect_find(self._items_list, item)
            if index is not None:
                del self._items_list[index]
            self._items_set.remove(item)

    def reverse(self) -> Iterator[T]:
        yield from reversed(self._items_list)

    def __iter__(self) -> Iterator[T]:
        yield from self._items_list


def bisect_find(items: List[T], x: T) -> Optional[int]:
    start = 0
    stop = len(items)
    while True:
        if start == stop:
            if items[start] == x:
                return start
            else:
                return None
        middle = start + stop // 2
        if items[middle] < x:
            start = middle + 1
        else:
            stop = middle
