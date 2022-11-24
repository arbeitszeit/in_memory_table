from __future__ import annotations

import random
import string
from dataclasses import dataclass, field
from timeit import timeit
from typing import Any, Callable, Iterator, Optional, Set, TypeVar
from unittest import TestCase
from uuid import UUID, uuid4

from .table import Table

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

    def test_can_order_users_by_name(self) -> None:
        expected_names = ["a", "c", "e", "b", "a"]
        address = self.db.create_address(street="", district="")
        for name in expected_names:
            self.db.create_user(name=name, address=address.id)
        assert [user.name for user in self.db.get_users().ordered_by_name()] == sorted(
            expected_names
        )

    def test_can_order_users_by_name_in_reverse_order(self) -> None:
        expected_names = ["a", "c", "e", "b", "a"]
        address = self.db.create_address(street="", district="")
        for name in expected_names:
            self.db.create_user(name=name, address=address.id)
        assert [
            user.name for user in self.db.get_users().ordered_by_name(reverse=True)
        ] == sorted(expected_names, reverse=True)


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
        return AddressQuery(
            items=lambda: self.addresses.all_items, db=self, ordering=None
        )

    def get_users(self) -> UserQuery:
        return UserQuery(items=lambda: self.users.all_items, db=self, ordering=None)


@dataclass
class Ordering:
    column: str
    table: str
    reverse: bool = False
    key: Optional[Callable[[Any], Any]] = None


class UUIDQuery:
    def __init__(
        self, items: Callable[[], Set[UUID]], db: Database, ordering: Optional[Ordering]
    ):
        self._items = items
        self.db = db
        self.ordering = ordering

    def with_id(self: UUIDQueryT, id_: UUID) -> UUIDQueryT:
        def new_items():
            return self._items() & {
                id_,
            }

        return type(self)(
            items=new_items,
            db=self.db,
            ordering=self.ordering,
        )

    def _get_ordered_items(self) -> Iterator[UUID]:
        if self.ordering:
            items = self._items()
            table = getattr(self.db, self.ordering.table)
            yield from (
                item
                for item in table.get_rows_ordered_by_column(
                    self.ordering.column,
                    key=self.ordering.key,
                    reverse=self.ordering.reverse,
                )
                if item in items
            )
        else:
            yield from self._items()

    def __len__(self) -> int:
        return len(self._items())


class UserQuery(UUIDQuery):
    def __iter__(self) -> Iterator[User]:
        yield from (self.db.users[item] for item in self._get_ordered_items())

    def with_name(self, name: str) -> UserQuery:
        def new_items() -> Set[UUID]:
            return self._items() & self.db.users.get_row_by_index_column("name", name)

        return type(self)(
            items=new_items,
            db=self.db,
            ordering=self.ordering,
        )

    def from_district(self, district: str) -> UserQuery:
        def new_items() -> Set[UUID]:
            addresses = set(self.db.get_addresses().in_district(district).ids())
            results: Set[UUID] = set()
            for address in addresses:
                results.update(
                    self.db.users.get_row_by_index_column("address", address)
                )
            return results & self._items()

        return type(self)(
            items=new_items,
            db=self.db,
            ordering=self.ordering,
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
            del self.db.users[item]
        return len(items)

    def ids(self) -> IdQuery:
        return IdQuery(
            items=self._items,
            db=self.db,
            ordering=self.ordering,
        )

    def ordered_by_name(self, reverse: bool = False) -> UserQuery:
        return type(self)(
            items=self._items,
            db=self.db,
            ordering=Ordering(
                "name",
                table="users",
                reverse=reverse,
            ),
        )


class IdQuery(UUIDQuery):
    def __iter__(self) -> Iterator[UUID]:
        yield from self._items()


class AddressQuery(UUIDQuery):
    def __iter__(self) -> Iterator[Address]:
        for item in self._get_ordered_items():
            yield self.db.addresses[item]

    def in_district(self, district: str) -> AddressQuery:
        def new_items() -> Set[UUID]:
            return self._items() & self.db.addresses.get_row_by_index_column(
                "district", district
            )

        return type(self)(
            db=self.db,
            items=new_items,
            ordering=self.ordering,
        )

    def ids(self) -> IdQuery:
        return IdQuery(
            items=self._items,
            db=self.db,
            ordering=self.ordering,
        )


def print_timing(
    label: str,
    function: Callable[[], None],
):
    result = timeit(function, number=100)
    print(label, result * 10000, "\u03BCs")


def null(o: Any) -> None:
    pass


def main() -> None:
    n = 10000
    print(f"#entries = {n}")
    db = Database()
    names = list(
        "".join(random.choice(string.ascii_letters) for _ in range(10))
        for _ in range(100)
    )
    streets = list(
        "".join(random.choice(string.ascii_letters) for _ in range(10))
        for _ in range(100)
    )
    districts = list(
        "".join(random.choice(string.ascii_letters) for _ in range(10))
        for _ in range(100)
    )
    for _ in range(n):
        street = random.choice(streets)
        district = random.choice(districts)
        db.create_address(street=street, district=district)
    addresses = list(db.get_addresses())
    print(f"created {n} addresses")
    for _ in range(n):
        name = random.choice(names)
        db.create_user(name=name, address=random.choice(addresses).id)
    print(f"created {n} users")
    print_timing(
        "address.with_id", lambda: null(list(db.get_addresses().with_id(uuid4())))
    )
    print_timing(
        "address.in_district",
        lambda: null(list(db.get_addresses().in_district("abc"))),
    )
    print_timing(
        "user.from_district",
        lambda: null(list(db.get_users().from_district("test"))),
    )
    print_timing(
        "user.increase_login_count",
        lambda: null(db.get_users().increase_login_count()),
    )
    print_timing("user.count", lambda: null(len(db.get_users())))
    print_timing(
        "user.ordered_by_name",
        lambda: null(list(db.get_users().ordered_by_name())),
    )


if __name__ == "__main__":
    main()
