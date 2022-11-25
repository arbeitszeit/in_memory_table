from __future__ import annotations

from dataclasses import fields
from typing import (
    Any,
    Dict,
    Generic,
    Hashable,
    Iterator,
    List,
    Optional,
    Protocol,
    Set,
    Type,
    TypeVar,
)

from .column_index import ColumnIndex, Indexable


class HasId(Protocol):
    @property
    def id(self) -> Hashable:
        ...


Row = TypeVar("Row", bound=HasId)


class Table(Generic[Row]):
    __slots__ = ("rows", "all_items", "column_indices")

    def __init__(
        self, cls: Type[Row], no_index_fields: Optional[List[str]] = None
    ) -> None:
        """Create a new Table from a dataclass cls. cls must provide
        an id field. Every field of cls will be indexed unless the
        field name is in no_index_fields.
        """
        blacklist: Set[str] = set(no_index_fields or [])
        blacklist.add("id")
        indexed_columns: Set[str] = {field.name for field in fields(cls)} - blacklist
        self.rows: Dict[Hashable, Any] = dict()
        self.all_items: Set[Hashable] = set()
        self.column_indices: Dict[str, ColumnIndex] = {
            field: ColumnIndex() for field in indexed_columns
        }

    def get_row_by_index_column(self, column: str, value: Indexable) -> Set[Hashable]:
        """Get all ids where the row has a specific value in the
        specified column.
        """
        index = self.column_indices.get(column)
        if index is None:
            raise ValueError(f"Column {column} is not indexed")
        return index[value]

    def add_row(self, row: Row) -> None:
        """Add a row to the table. The caller has to make sure the the
        id of the specified row is not yet in the database."""
        id_ = row.id
        if id_ in self.rows:
            raise ValueError(f"Row with id {id_} is already present in table")
        self.rows[id_] = row
        self.all_items.add(id_)
        for column in self.column_indices:
            column_value = getattr(row, column)
            self.column_indices[column].add_item(column_value, id_)

    def update_row(self, id_: Hashable, **values: Indexable) -> None:
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
            if column not in self.column_indices:
                continue
            self.column_indices[column].remove_item(old_value, id_)
            self.column_indices[column].add_item(value, id_)

    def delete_row(self, id_: Hashable) -> Optional[Row]:
        """The dataclass instance stored in that row will be returned.
        Trying to delete a non existing row will do nothing and None
        is returned."""
        row = self.rows.get(id_)
        if row is None:
            return None
        for column in self.column_indices:
            self.column_indices[column].remove_item(getattr(row, column), id_)
        self.all_items.remove(id_)
        del self.rows[id_]
        return row

    def get_rows_sorted_by_column(
        self,
        column: str,
        *,
        reverse: bool = False,
    ) -> Iterator[Hashable]:
        """Return all ids sorted by the value in the specified
        column. The reverse argument function equivalent to the
        reverse arguments of the sorted function.  If reverse is set
        to True then the sorting order is reversed.

        """
        yield from self.column_indices[column].get_sorted_items(reverse=reverse)

    def __getitem__(self, key: Hashable) -> Row:
        return self.rows[key]

    def __contains__(self, key: Hashable) -> bool:
        return key in self.rows

    def __delitem__(self, key: Hashable) -> None:
        self.delete_row(key)
