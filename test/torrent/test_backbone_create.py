from os import path

import tcm

from clot import torrent


class CreateTestCase(tcm.TestCase):
    @tcm.values(
        (None,  'cannot be decoded'),
        ({},    'cannot be decoded'),
    )
    def test_bad_value_types_will_raise_type_error(self, raw_bytes, expected_message):
        with self.assertRaises(TypeError) as outcome:
            torrent.parse(raw_bytes)
        message = outcome.exception.args[0]
        self.assertIn(expected_message, message)

    @tcm.values(
        (b'',               'value is empty'),
        (b'le',             'expected top-level dictionary'),
        (b'd',              'missing dict value terminator'),
        (b'di6e4:Oopse',    'unsupported key type'),
    )
    def test_bad_values_will_raise_value_error(self, raw_bytes, expected_message):
        with self.assertRaises(ValueError) as outcome:
            torrent.parse(raw_bytes)
        message = outcome.exception.args[0]
        self.assertIn(expected_message, message)


class LoadTestCase(tcm.TestCase):
    def test_empty_file_will_raise(self):
        with self.assertRaises(ValueError) as outcome:
            torrent.load(self.data('empty_file.torrent'))
        message = outcome.exception.args[0]
        self.assertIn('value is empty', message)

    def test_empty_dict_will_not_raise(self):
        t = torrent.load(self.data('empty_dict.torrent'))
        self.assertDictEqual(t.data, {})
        self.assertTrue(t.file_path.endswith('empty_dict.torrent'))

    @staticmethod
    def data(file_path):
        my_dir = path.dirname(__file__)
        return path.join(my_dir, 'data', file_path)
