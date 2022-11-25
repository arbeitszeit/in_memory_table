from unittest import TestCase

from in_memory_table.sorted_collection import SortedCollection


class SortedCollectionTests(TestCase):
    def test_that_empty_tree_is_considered_false(self) -> None:
        assert not SortedCollection()

    def test_that_tree_is_considered_true_after_adding_an_element(self) -> None:
        tree: SortedCollection[int] = SortedCollection()
        tree.add(1)
        assert tree

    def test_has_length_2_after_adding_two_elements(self) -> None:
        tree: SortedCollection[int] = SortedCollection()
        tree.add(1)
        tree.add(2)
        assert len(tree) == 2

    def test_iterating_over_empty_tree_yields_empty_iterator(self) -> None:
        assert not list(SortedCollection())

    def test_adding_1_to_tree_and_then_iterating_over_it_yields_only_one_in_iterator(
        self,
    ) -> None:
        tree: SortedCollection[int] = SortedCollection()
        tree.add(1)
        assert list(tree) == [1]

    def test_adding_2_1_to_tree_and_then_iterating_over_it_yields_1_2_in_iterator(
        self,
    ) -> None:
        tree: SortedCollection[int] = SortedCollection()
        tree.add(2)
        tree.add(1)
        assert list(tree) == [1, 2]

    def test_adding_1_2_3_to_tree_and_then_removing_two_yields_tree_with_1_and_3(
        self,
    ) -> None:
        tree: SortedCollection[int] = SortedCollection()
        tree.add(1)
        tree.add(2)
        tree.add(3)
        tree.remove(2)
        assert list(tree) == [1, 3]

    def test_adding_1_to_tree_and_then_removing_two_yields_tree_with_1(
        self,
    ) -> None:
        tree: SortedCollection[int] = SortedCollection()
        tree.add(1)
        tree.remove(2)
        assert list(tree) == [1]

    def test_adding_1_4_3_to_tree_and_then_removing_two_yields_tree_with_reversed_order_of_4_3_1(
        self,
    ) -> None:
        tree: SortedCollection[int] = SortedCollection()
        tree.add(1)
        tree.add(4)
        tree.add(3)
        assert list(tree.reverse()) == [4, 3, 1]

    def test_adding_1_1_2_2_to_tree_yields_tree_with_1_2_in_it(self) -> None:
        tree: SortedCollection[int] = SortedCollection()
        tree.add(1)
        tree.add(1)
        tree.add(2)
        tree.add(2)
        assert list(tree) == [1, 2]
