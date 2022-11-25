from __future__ import annotations

from collections import defaultdict
from typing import Generic, Hashable, Iterator, Protocol, Set, TypeVar

from .sorted_collection import SortedCollection

IndexableT = TypeVar("IndexableT", bound="Indexable")
HashableT = TypeVar("HashableT", bound=Hashable)


class Indexable(Hashable, Protocol):
    def __lt__(self: IndexableT, other: IndexableT) -> bool:
        pass


class ColumnIndex(Generic[HashableT]):
    def __init__(self) -> None:
        self._index: defaultdict[Indexable, Set[HashableT]] = defaultdict(set)
        self._sorted_values: SortedCollection[Indexable] = SortedCollection()

    def get_sorted_items(
        self,
        *,
        reverse: bool = False,
    ) -> Iterator[Hashable]:
        if reverse:
            keys = self._sorted_values.reverse()
        else:
            keys = iter(self._sorted_values)
        for value in keys:
            yield from self._index[value]

    def remove_item(self, key: Indexable, id_: HashableT) -> None:
        """Remove an item from the index"""
        ids = self._index[key]
        ids.remove(id_)
        if not ids:
            self._sorted_values.remove(key)

    def add_item(self, key: Indexable, id_: HashableT) -> None:
        """Add an item to the index"""
        self._index[key].add(id_)
        self._sorted_values.add(key)

    def __getitem__(self, key: Indexable) -> Set[HashableT]:
        return self._index[key]
