from os import path

import tcm

from clot import torrent


class CreateTestCase(tcm.TestCase):
    def test_new_torrent_has_expected_values(self):
        t = torrent.new()
        self.assertDictEqual(t.data, {})
        self.assertIsNone(t.file_path)

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

    @tcm.values(
        (b'de',                 {}),
        (b'd7:comment2:Hie',    {'comment': b'Hi'}),
        (b'd7:unknown4:Oopse',  {'unknown': b'Oops'}),
    )
    def test_bencoded_dict_is_accepted(self, raw_bytes, expected_dict):
        t = torrent.parse(raw_bytes)
        self.assertDictEqual(t.data, expected_dict)
        self.assertIsNone(t.file_path)


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
