"""This module is not meant for public consumption but instead only a
tool to asses the performance impact of implementation details.
"""

from __future__ import annotations

import random
import string
from timeit import timeit
from typing import Any, Callable
from uuid import uuid4

from .test_database import Database


def print_timing(
    label: str,
    function: Callable[[], None],
) -> None:
    result = timeit(function, number=100)
    print(label, result * 10000, "\u03BCs")


def null(o: Any) -> None:
    pass


def random_string():
    return "".join(random.choice(string.ascii_letters) for _ in range(10))


def main() -> None:
    n = 10000
    print(f"#entries = {n}")
    db = Database()
    names = list(random_string() for _ in range(100))
    streets = list(random_string() for _ in range(100))
    districts = list(random_string() for _ in range(100))
    for _ in range(n):
        street = random.choice(streets)
        district = random.choice(districts)
        db.create_address(street=street, district=district)
    addresses = list(db.get_addresses())
    print(f"created {n} addresses")
    example_district = random.choice(district)
    for _ in range(n):
        name = random.choice(names)
        db.create_user(name=name, address=random.choice(addresses).id)
    print(f"created {n} users")
    print_timing(
        "address.with_id (non-existing)",
        lambda: null(list(db.get_addresses().with_id(uuid4()))),
    )
    print_timing(
        "address.in_district",
        lambda: null(list(db.get_addresses().in_district(example_district))),
    )
    print_timing(
        "user.from_district",
        lambda: null(list(db.get_users().from_district(example_district))),
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
