from __future__ import annotations

from collections import defaultdict
from typing import Hashable, Iterator, Protocol, Set, TypeVar
from uuid import UUID

from .sorted_collection import SortedCollection

IndexableT = TypeVar("IndexableT", bound="Indexable")


class Indexable(Hashable, Protocol):
    def __lt__(self: IndexableT, other: IndexableT) -> bool:
        pass


class ColumnIndex:
    def __init__(self) -> None:
        self._index: defaultdict[Indexable, Set[UUID]] = defaultdict(set)
        self._sorted_values: SortedCollection[Indexable] = SortedCollection()

    def get_sorted_items(
        self,
        *,
        reverse: bool = False,
    ) -> Iterator[UUID]:
        if reverse:
            keys = self._sorted_values.reverse()
        else:
            keys = iter(self._sorted_values)
        for value in keys:
            yield from self._index[value]

    def remove_item(self, key: Indexable, id_: UUID) -> None:
        """Remove an item from the index"""
        ids = self._index[key]
        ids.remove(id_)
        if not ids:
            self._sorted_values.remove(key)

    def add_item(self, key: Indexable, id_: UUID) -> None:
        """Add an item to the index"""
        self._index[key].add(id_)
        self._sorted_values.add(key)

    def __getitem__(self, key: Indexable) -> Set[UUID]:
        return self._index[key]
