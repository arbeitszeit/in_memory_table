from dataclasses import dataclass, field
from unittest import TestCase
from uuid import UUID, uuid4

from in_memory_relations.table import Table


class TableTests(TestCase):
    @dataclass
    class Model:
        id: UUID = field(default_factory=uuid4)
        x: int = 0
        y: str = ""

    def setUp(self) -> None:
        self.table = Table(cls=self.Model)

    def test_that_added_rows_can_be_retrieved(self) -> None:
        row = self.Model()
        self.table.add_row(row)
        assert self.table[row.id] == row

    def test_that_row_id_can_be_retrieved_by_column_value(self) -> None:
        expected_x = 123
        expected_y = "123"
        row = self.Model(x=expected_x, y=expected_y)
        self.table.add_row(row)
        assert row.id in self.table.get_row_by_index_column("x", expected_x)
        assert row.id not in self.table.get_row_by_index_column("x", 7654)
        assert row.id in self.table.get_row_by_index_column("y", expected_y)
        assert row.id not in self.table.get_row_by_index_column("x", "different value")

    def test_trying_to_get_items_for_non_existing_column_raises_value_error(
        self,
    ) -> None:
        with self.assertRaises(ValueError):
            self.table.get_row_by_index_column("non existing column", 1)

    def test_trying_to_get_items_with_with_column_values_not_in_table_yields_empty_set(
        self,
    ) -> None:
        assert not self.table.get_row_by_index_column("x", 1)

    def test_updating_a_row_means_that_records_returned_from_table_reflect_the_change(
        self,
    ) -> None:
        old_x = 1
        new_x = 2
        model = self.Model(x=old_x)
        self.table.add_row(model)
        self.table.update_row(model.id, x=new_x)
        assert self.table[model.id].x == new_x

    def test_updating_a_row_means_that_records_cannot_be_found_under_old_column_values(
        self,
    ) -> None:
        old_x = 1
        new_x = 2
        model = self.Model(x=old_x)
        self.table.add_row(model)
        self.table.update_row(model.id, x=new_x)
        assert not self.table.get_row_by_index_column("x", old_x)

    def test_updating_a_row_means_that_records_can_be_found_under_new_column_values(
        self,
    ) -> None:
        old_x = 1
        new_x = 2
        model = self.Model(x=old_x)
        self.table.add_row(model)
        self.table.update_row(model.id, x=new_x)
        assert self.table.get_row_by_index_column("x", new_x)

    def test_cannot_retrieve_models_that_where_deleted(self) -> None:
        model = self.Model()
        self.table.add_row(model)
        self.table.delete_row(model.id)
        with self.assertRaises(KeyError):
            self.table[model.id]

    def test_that_model_other_models_are_not_deleted(self) -> None:
        model = self.Model()
        other_model = self.Model()
        self.table.add_row(model)
        self.table.add_row(other_model)
        self.table.delete_row(model.id)
        assert self.table[other_model.id]

    def test_that_ids_can_be_retrieved_in_order(self) -> None:
        models = [self.Model(x=x) for x in [1, 6, 3, 4, 2, 5, 7]]
        for model in models:
            self.table.add_row(model)
        models.sort(key=lambda m: m.x)
        assert [model.id for model in models] == list(
            self.table.get_rows_sorted_by_column("x")
        )
