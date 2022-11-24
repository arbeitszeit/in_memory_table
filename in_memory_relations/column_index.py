from __future__ import annotations

from collections import defaultdict
from typing import Callable, Hashable, Iterator, Optional, Protocol, Set, TypeVar
from uuid import UUID

IndexableT = TypeVar("IndexableT", bound="Indexable")


class Indexable(Hashable, Protocol):
    def __lt__(self: IndexableT, other: IndexableT) -> bool:
        pass


class ColumnIndex:
    def __init__(self) -> None:
        self._index: defaultdict[Indexable, Set[UUID]] = defaultdict(set)

    def get_sorted_items(
        self,
        *,
        key: Optional[Callable[[Indexable], bool]] = None,
        reverse: bool = False,
    ) -> Iterator[UUID]:
        values = sorted(self._index.keys(), key=key, reverse=reverse)
        for value in values:
            yield from self._index[value]

    def remove_item(self, key: Indexable, id_: UUID) -> None:
        """Remove an item from the index"""
        self._index[key].remove(id_)

    def add_item(self, key: Indexable, id_: UUID) -> None:
        """Add an item to the index"""
        self._index[key].add(id_)

    def __getitem__(self, key: Indexable) -> Set[UUID]:
        return self._index[key]
