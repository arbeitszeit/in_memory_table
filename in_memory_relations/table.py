from __future__ import annotations

from collections import defaultdict
from dataclasses import fields
from typing import Any, Dict, Generic, Hashable, List, Optional, Type, TypeVar
from uuid import UUID

from .ordered_set import OrderedSet

T = TypeVar("T")


class Table(Generic[T]):
    __slots__ = ("indexed_columns", "rows", "all_items", "column_indices")

    def __init__(
        self, cls: Type[T], no_index_fields: Optional[List[str]] = None
    ) -> None:
        """Create a new Table from a dataclass cls. cls must provide
        an id field. Every field of cls will be indexed unless the
        field name is in no_index_fields.
        """
        blacklist = set(no_index_fields or [])
        blacklist.add("id")
        self.indexed_columns = {field.name for field in fields(cls)} - blacklist
        self.rows: Dict[UUID, Any] = dict()
        self.all_items: OrderedSet[UUID] = OrderedSet()
        self.column_indices: Dict[str, Dict[Any, OrderedSet[Any]]] = {
            field: defaultdict(lambda: OrderedSet()) for field in self.indexed_columns
        }

    def get_row_by_index_column(self, column: str, value: Hashable) -> OrderedSet[UUID]:
        return self.column_indices[column][value]

    def add_row(self, id_: UUID, row: T) -> None:
        if id_ in self.rows:
            raise ValueError(f"Row with id {id_} is already present in table")
        self.rows[id_] = row
        self.all_items.add(id_)
        for column in self.column_indices:
            column_value = getattr(row, column)
            self.column_indices[column][column_value].add(id_)

    def update_row(self, id_: UUID, **values) -> None:
        """All keyword arguments except id_ must be field names of of
        the indexed dataclass in this table. id may not be
        updated. Trying to update a non existing row will do nothing.
        """
        if "id" in values:
            raise ValueError("Change of id field was requested, which is illegal.")
        row = self.rows.get(id_)
        if row is None:
            return
        for column, value in values.items():
            old_value = getattr(row, column)
            setattr(row, column, value)
            if column not in self.indexed_columns:
                continue
            self.column_indices[column][old_value].remove(id_)
            self.column_indices[column][value].add(id_)

    def delete_row(self, id_: UUID) -> Optional[T]:
        """The dataclass instance stored in that row will be returned.
        Trying to delete a non existing row will do nothing and None
        is returned."""
        row = self.rows.get(id_)
        if row is None:
            return None
        for column in self.indexed_columns:
            self.column_indices[column][getattr(row, column)].remove(id_)
        self.all_items.remove(id_)
        del self.rows[id_]
        return row

    def __getitem__(self, key: UUID) -> T:
        return self.rows[key]

    def __contains__(self, key: UUID) -> bool:
        return key in self.rows

    def __delitem__(self, key: UUID) -> None:
        self.delete_row(key)
