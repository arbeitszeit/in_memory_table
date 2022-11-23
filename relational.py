from __future__ import annotations

import random
import string
from collections import OrderedDict, defaultdict
from dataclasses import dataclass, field, fields
from timeit import timeit
from typing import (
    Any,
    Callable,
    Dict,
    Generic,
    Hashable,
    Iterable,
    Iterator,
    List,
    Optional,
    Type,
    TypeVar,
)
from unittest import TestCase
from uuid import UUID, uuid4

T = TypeVar("T", bound="Hashable")
UUIDQueryT = TypeVar("UUIDQueryT", bound="UUIDQuery")


class Tests(TestCase):
    def setUp(self) -> None:
        self.db = Database()

    def test_get_no_addresses_on_empty_db(self) -> None:
        assert not self.db.get_addresses()

    def test_get_at_least_one_address_after_an_address_was_created(self) -> None:
        self.db.create_address(
            street="",
            district="",
        )
        assert self.db.get_addresses()

    def test_result_can_be_filtered_by_id(self) -> None:
        self.db.create_address(
            street="",
            district="",
        )
        assert not self.db.get_addresses().with_id(uuid4())

    def test_can_filter_users_by_district(self) -> None:
        expected_district = "berlin"
        address = self.db.create_address(street="", district=expected_district)
        self.db.create_user(name="", address=address.id)
        assert self.db.get_users().from_district(expected_district)
        assert not self.db.get_users().from_district("other_district")

    def test_can_filter_addresses_by_district(self) -> None:
        self.db.create_address(street="", district="berlin")
        assert self.db.get_addresses().in_district("berlin")
        assert not self.db.get_addresses().in_district("brandenburg")

    def test_can_filter_user_by_name(self) -> None:
        expected_name = "testname"
        address = self.db.create_address(street="", district="")
        self.db.create_user(name=expected_name, address=address.id)
        assert self.db.get_users().with_name(expected_name)
        assert not self.db.get_users().with_name("other_name")

    def test_user_have_login_counter_of_0_after_being_created(self) -> None:
        address = self.db.create_address(street="", district="")
        user = self.db.create_user(name="name", address=address.id)
        user.login_counter == 0

    def test_can_increase_login_count(self) -> None:
        address = self.db.create_address(street="", district="")
        self.db.create_user(name="name", address=address.id)
        self.db.get_users().increase_login_count()
        assert all([user.login_counter == 1 for user in self.db.get_users()])

    def test_can_delete_user(self) -> None:
        address = self.db.create_address(street="", district="")
        self.db.create_user(name="delete me", address=address.id)
        self.db.create_user(name="", address=address.id)
        deleted_rows = self.db.get_users().with_name("delete me").delete()
        assert deleted_rows == 1
        assert len(self.db.get_users()) == 1
        assert not self.db.get_users().with_name("delete me")


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


@dataclass(slots=True)
class Address:
    id: UUID
    street: str
    district: str


@dataclass(slots=True)
class User:
    id: UUID
    name: str
    address: UUID
    login_counter: int = field(default=0)


class UUIDQuery:
    def __init__(self, items: Callable[[], OrderedSet[UUID]], db: Database):
        self._items = items
        self.db = db

    def with_id(self: UUIDQueryT, id_: UUID) -> UUIDQueryT:
        def new_items():
            return self._items() & OrderedSet.from_iter([id_])

        return type(self)(
            items=new_items,
            db=self.db,
        )

    def __len__(self) -> int:
        return len(self._items())


class UserQuery(UUIDQuery):
    def __iter__(self) -> Iterator[User]:
        for item in self._items():
            yield self.db.users[item]

    def with_name(self, name: str) -> UserQuery:
        def new_items() -> OrderedSet[UUID]:
            return self._items() & self.db.users.get_by_column("name", name)

        return type(self)(
            items=new_items,
            db=self.db,
        )

    def from_district(self, district: str) -> UserQuery:
        def new_items() -> OrderedSet[UUID]:
            addresses = set(self.db.get_addresses().in_district(district).ids())
            results: OrderedSet[UUID] = OrderedSet()
            for address in addresses:
                results.extend(self.db.users.get_by_column("address", address))
            return results & self._items()

        return type(self)(
            items=new_items,
            db=self.db,
        )

    def increase_login_count(self) -> int:
        items = self._items()
        for user_id in items:
            user_model = self.db.users[user_id]
            self.db.users.update_row(
                id_=user_id, login_counter=user_model.login_counter + 1
            )
        return len(items)

    def delete(self) -> int:
        items = self._items()
        for item in items:
            self.db.users.delete_row(item)
        return len(items)

    def ids(self) -> IdQuery:
        return IdQuery(
            items=self._items,
            db=self.db,
        )


class IdQuery(UUIDQuery):
    def __iter__(self) -> Iterator[UUID]:
        yield from self._items()


class AddressQuery(UUIDQuery):
    def __iter__(self) -> Iterator[Address]:
        for item in self._items():
            yield self.db.addresses[item]

    def in_district(self, district: str) -> AddressQuery:
        def new_items() -> OrderedSet:
            return self._items() & self.db.addresses.get_by_column("district", district)

        return type(self)(
            db=self.db,
            items=new_items,
        )

    def ids(self) -> IdQuery:
        return IdQuery(
            items=self._items,
            db=self.db,
        )


class Table:
    __slots__ = ("indexed_columns", "rows", "all_items", "column_indices")

    def __init__(self, cls: Type, no_index_fields: Optional[List[str]] = None) -> None:
        blacklist = set(no_index_fields or [])
        blacklist.add("id")
        self.indexed_columns = {field.name for field in fields(cls)} - blacklist
        self.rows: Dict[UUID, Any] = dict()
        self.all_items: OrderedSet[UUID] = OrderedSet()
        self.column_indices: Dict[str, Dict[Any, OrderedSet[Any]]] = {
            field: defaultdict(lambda: OrderedSet()) for field in self.indexed_columns
        }

    def get_by_column(self, column: str, value) -> OrderedSet[UUID]:
        return self.column_indices[column][value]

    def add_row(self, id_: UUID, row: Any):
        if id_ in self.rows:
            raise ValueError(f"Row with id {id_} is already present in table")
        self.rows[id_] = row
        self.all_items.add(id_)
        for column in self.column_indices:
            column_value = getattr(row, column)
            self.column_indices[column][column_value].add(id_)

    def update_row(self, id_: UUID, **values):
        row = self.rows[id_]
        for column, value in values.items():
            old_value = getattr(row, column)
            setattr(row, column, value)
            if column not in self.indexed_columns:
                continue
            self.column_indices[column][old_value].remove(id_)
            self.column_indices[column][value].add(id_)

    def delete_row(self, id_: UUID):
        row = self.rows[id_]
        for column in self.indexed_columns:
            self.column_indices[column][getattr(row, column)].remove(id_)
        self.all_items.remove(id_)
        del self.rows[id_]
        return row

    def __getitem__(self, key: UUID):
        return self.rows[key]

    def __contains__(self, key: UUID) -> bool:
        return key in self.rows

    def __delitem__(self, key: UUID) -> None:
        self.all_items.remove(key)
        row = self.rows[key]
        for column in self.indexed_columns:
            del self.column_indices[column][getattr(row, column)]
        del self.rows[key]


@dataclass
class Database:
    users: Table = field(
        default_factory=lambda: Table(cls=User, no_index_fields=["login_counter"])
    )
    addresses: Table = field(default_factory=lambda: Table(cls=Address))

    def create_address(self, *, street: str, district: str) -> Address:
        item = Address(
            id=uuid4(),
            street=street,
            district=district,
        )
        self.addresses.add_row(id_=item.id, row=item)
        return item

    def create_user(self, *, name: str, address: UUID) -> User:
        assert address in self.addresses
        user = User(
            id=uuid4(),
            name=name,
            address=address,
        )
        self.users.add_row(id_=user.id, row=user)
        return user

    def get_addresses(self) -> AddressQuery:
        return AddressQuery(items=lambda: self.addresses.all_items, db=self)

    def get_users(self) -> UserQuery:
        return UserQuery(items=lambda: self.users.all_items, db=self)


def print_timing(
    label: str,
    function: Callable[[], None],
):
    result = timeit(function, number=100)
    print(label, result * 10000, "\u03BCs")


def main():
    n = 10000
    print(f"#entries = {n}")
    db = Database()
    for _ in range(n):
        street = "".join(random.choice(string.ascii_letters) for _ in range(10))
        district = "".join(random.choice(string.ascii_letters) for _ in range(10))
        address = db.create_address(street=street, district=district)
        name = "".join(random.choice(string.ascii_letters) for _ in range(10))
        db.create_user(name=name, address=address.id)
        name = "".join(random.choice(string.ascii_letters) for _ in range(10))
        db.create_user(name=name, address=address.id)
    print_timing("address.with_id", lambda: bool(db.get_addresses().with_id(uuid4())))
    print_timing(
        "address.in_district",
        lambda: bool(db.get_addresses().in_district("abc")),
    )
    print_timing(
        "user.from_district",
        lambda: bool(db.get_users().from_district(uuid4())),
    )
    print_timing(
        "user.increase_login_count",
        lambda: db.get_users().increase_login_count(),
    )
    print_timing("user.count", lambda: len(db.get_users()))


if __name__ == "__main__":
    main()
