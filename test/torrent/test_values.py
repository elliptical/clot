import tcm

from clot.torrent.values import List


class TestCase(tcm.TestCase):
    @staticmethod
    def valid_item(value):
        if isinstance(value, int) and value > 0:
            return value
        raise ValueError(f'invalid item {value}')

    def test_list_can_be_created_with_zero_or_more_values_and_is_iterable(self):
        x = List(self.valid_item)
        self.assertEqual(len(x), 0)
        self.assertEqual(repr(x), 'List([])')

        x = List(self.valid_item, 3)
        self.assertEqual(len(x), 1)
        self.assertEqual(repr(x), 'List([3])')
        self.assertListEqual(list(x), [3])

        x = List(self.valid_item, 3, 1, 2)
        self.assertEqual(len(x), 3)
        self.assertEqual(repr(x), 'List([3, 1, 2])')
        self.assertTupleEqual(tuple(x), (3, 1, 2))

    def test_list_can_grow(self):
        x = List(self.valid_item)

        x.append(10)
        x.insert(0, 20)
        x.extend([30, 40])
        x.insert(4, 50)
        x.insert(-1, 60)
        self.assertListEqual(list(x), [20, 10, 30, 40, 60, 50])
        self.assertEqual(repr(x), 'List([20, 10, 30, 40, 60, 50])')

    def test_list_can_be_indexed(self):
        x = List(self.valid_item, 20, 10)
        self.assertListEqual(list(x), [20, 10])
        self.assertEqual(x[1], 10)
        self.assertEqual(x[-2], 20)

        x[1] = 30
        self.assertListEqual(list(x), [20, 30])
        self.assertListEqual(x[1:], [30])

        del x[1]
        self.assertListEqual(list(x), [20])

        x[1:] = (3, 4, 5)
        self.assertListEqual(list(x), [20, 3, 4, 5])
        self.assertListEqual(x[:], [20, 3, 4, 5])
        self.assertListEqual(list(x[:-1]), [20, 3, 4])

        del x[::2]
        self.assertListEqual(list(x), [3, 5])

        with self.assertRaises(IndexError) as outcome:
            _ = x[2]
        message = outcome.exception.args[0]
        self.assertEqual(message, 'list index out of range')

        with self.assertRaises(IndexError) as outcome:
            x[2] = 1
        message = outcome.exception.args[0]
        self.assertEqual(message, 'list assignment index out of range')

        with self.assertRaises(ValueError) as outcome:
            x[2] = 0
        message = outcome.exception.args[0]
        self.assertEqual(message, 'invalid item 0')     # value checked before index

    def test_invalid_items_will_raise(self):
        with self.assertRaises(ValueError) as outcome:
            List(self.valid_item, 1, 2, -3)
        message = outcome.exception.args[0]
        self.assertEqual(message, 'invalid item -3')

        x = List(self.valid_item, 1, 2, 3)

        with self.assertRaises(ValueError) as outcome:
            x.append(-3)
        message = outcome.exception.args[0]
        self.assertEqual(message, 'invalid item -3')

        with self.assertRaises(ValueError) as outcome:
            x[0] = -3
        message = outcome.exception.args[0]
        self.assertEqual(message, 'invalid item -3')
