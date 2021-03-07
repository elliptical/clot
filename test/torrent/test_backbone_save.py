from contextlib import contextmanager
from datetime import datetime, timezone
from os import path, remove
from tempfile import NamedTemporaryFile
import textwrap

import tcm

from clot import bencode, torrent


SOME_BYTES = b'old garbage'


class SaveAsTestCase(tcm.TestCase):
    def test_new_file_is_created(self):
        t = torrent.new()
        t.data['my'] = 'value'

        with temp_file_path() as file_path:
            self.assertFalse(path.exists(file_path))

            t.save_as(file_path)
            self.assertEqual(t.file_path, file_path)
            self.assertTrue(path.exists(file_path))
            self.assertEqual(read_bytes(file_path), b'd2:my5:valuee')

    def test_existing_file_will_raise_by_default(self):
        t = torrent.new()
        t.data['my'] = 'value'

        with temp_file_path(contents=SOME_BYTES) as file_path:
            self.assertTrue(path.exists(file_path))
            self.assertEqual(read_bytes(file_path), SOME_BYTES)

            with self.assertRaises(FileExistsError):
                t.save_as(file_path)
            self.assertIsNone(t.file_path)
            self.assertEqual(read_bytes(file_path), SOME_BYTES)

    def test_existing_file_can_be_overwritten_when_asked(self):
        t = torrent.new()
        t.data['my'] = 'value'

        with temp_file_path(contents=SOME_BYTES) as file_path:
            self.assertTrue(path.exists(file_path))
            self.assertEqual(read_bytes(file_path), SOME_BYTES)

            t.save_as(file_path, overwrite=True)
            self.assertEqual(t.file_path, file_path)
            self.assertEqual(read_bytes(file_path), b'd2:my5:valuee')


class SaveTestCase(tcm.TestCase):
    def test_orphan_torrent_will_raise(self):
        t = torrent.parse(b'd2:my5:valuee')
        with self.assertRaises(Exception) as outcome:
            t.save()
        message = outcome.exception.args[0]
        self.assertEqual(message, 'expected a torrent loaded from file')

    def test_original_file_is_overwritten(self):
        with temp_file_path(contents=b'd2:my5:valuee') as file_path:
            t = torrent.load(file_path)
            t.data['my'] = 'modified'
            t.save()
            self.assertEqual(read_bytes(file_path), b'd2:my8:modifiede')

    def test_loaded_file_can_be_saved_elsewhere(self):
        with temp_file_path(contents=b'd2:my5:valuee') as file_path:
            t = torrent.load(file_path)
            t.data['my'] = 'modified'

            with temp_file_path() as new_file_path:
                t.save_as(new_file_path)
                self.assertEqual(t.file_path, new_file_path)
                self.assertEqual(read_bytes(new_file_path), b'd2:my8:modifiede')

            self.assertEqual(read_bytes(file_path), b'd2:my5:valuee')

    def test_creation_date_outputs_as_integer(self):
        t = torrent.new()
        t.creation_date = datetime(1970, 1, 1, 0, 0, 12, tzinfo=timezone.utc)

        with temp_file_path() as file_path:
            t.save_as(file_path)
            self.assertEqual(read_bytes(file_path), b'd13:creation datei12ee')

    @tcm.values(
        ([],                                    b'de'),
        (['http://host-1'],                     b'd8:url-list13:http://host-1e'),
        (['http://host-1', 'http://host-2'],    b'd8:url-listl13:http://host-113:http://host-2ee'),
    )
    def test_url_list_outputs_list_or_single_or_none(self, value, expected_bytes):
        raw_bytes = bencode.encode({'url-list': value})
        t = torrent.parse(raw_bytes)

        with temp_file_path() as file_path:
            t.save_as(file_path)
            self.assertEqual(read_bytes(file_path), expected_bytes)

    @tcm.values(
        ([],                b'de'),
        ([['host', 8080]],  b'd5:nodesll4:hosti8080eeee'),
    )
    def test_node_list_outputs_list_or_none(self, value, expected_bytes):
        raw_bytes = bencode.encode({'nodes': value})
        t = torrent.parse(raw_bytes)

        with temp_file_path() as file_path:
            t.save_as(file_path)
            self.assertEqual(read_bytes(file_path), expected_bytes)

    @tcm.values(
        ([],
            b'de'),

        ([['http://tracker'], ['http://one', 'http://two']],
            b'd13:announce-listll14:http://trackerel10:http://one10:http://twoeee'),
    )
    def test_announce_list_outputs_list_or_none(self, value, expected_bytes):
        raw_bytes = bencode.encode({'announce-list': value})
        t = torrent.parse(raw_bytes)

        with temp_file_path() as file_path:
            t.save_as(file_path)
            self.assertEqual(read_bytes(file_path), expected_bytes)


class DumpTestCase(tcm.TestCase):
    def test_existing_file_will_raise_by_default(self):
        t = torrent.new()

        with temp_file_path(contents=SOME_BYTES) as file_path:
            self.assertTrue(path.exists(file_path))
            self.assertEqual(read_bytes(file_path), SOME_BYTES)

            with self.assertRaises(FileExistsError):
                t.dump(file_path)
            self.assertEqual(read_bytes(file_path), SOME_BYTES)

    def test_existing_file_can_be_overwritten_when_asked(self):
        t = torrent.new()

        with temp_file_path(contents=SOME_BYTES) as file_path:
            self.assertTrue(path.exists(file_path))
            self.assertEqual(read_bytes(file_path), SOME_BYTES)

            t.dump(file_path, overwrite=True)
            self.assertEqual(read_str(file_path), '{}')

    def test_default_is_oneline_unsorted(self):
        t = torrent.new()
        t.data['my'] = 'value'
        t.data['many'] = [-1, 'two', {'x': 1, 'y': 2}]
        expected_json = '{"my": "value", "many": [-1, "two", {"x": 1, "y": 2}]}'

        with temp_file_path(suffix='.json') as file_path:
            self.assertFalse(path.exists(file_path))

            t.dump(file_path)
            self.assertIsNone(t.file_path)
            self.assertTrue(path.exists(file_path))
            self.assertEqual(read_str(file_path), expected_json)

    def test_output_can_be_multiline_indented_sorted(self):
        t = torrent.new()
        t.data['my'] = 'value'
        t.data['many'] = [-1, 'two', {'x': 1, 'y': 2}]
        expected_json = textwrap.dedent("""
            {
              "many": [
                -1,
                "two",
                {
                  "x": 1,
                  "y": 2
                }
              ],
              "my": "value"
            }
            """).strip()

        with temp_file_path(suffix='.json') as file_path:
            self.assertFalse(path.exists(file_path))

            t.dump(file_path, indent=2, sort_keys=True)
            self.assertIsNone(t.file_path)
            self.assertTrue(path.exists(file_path))
            self.assertEqual(read_str(file_path), expected_json)

    def test_bytes_output_as_string(self):
        t = torrent.new()
        t.data['x'] = b'value'      # plain ASCII
        t.data['y'] = b'\xab\xcd'   # not a valid UTF-8, will be hex in the output
        t.data['z'] = '\N{SHRUG}'   # 4-byte UTF-8
        expected_json = '{"x": "value", "y": "hex::abcd", "z": "' + '\N{SHRUG}' + '"}'

        with temp_file_path(suffix='.json') as file_path:
            self.assertFalse(path.exists(file_path))

            t.dump(file_path)
            self.assertIsNone(t.file_path)
            self.assertTrue(path.exists(file_path))
            self.assertEqual(read_str(file_path), expected_json)

    def test_creation_date_outputs_as_iso_string(self):
        raw_bytes = bencode.encode({'creation date': 0})
        t = torrent.parse(raw_bytes)
        expected_json = '{"creation date": "1970-01-01 00:00:00+00:00"}'

        with temp_file_path(suffix='.json') as file_path:
            self.assertFalse(path.exists(file_path))

            t.dump(file_path)
            self.assertIsNone(t.file_path)
            self.assertTrue(path.exists(file_path))
            self.assertEqual(read_str(file_path), expected_json)

    @tcm.values(
        ([],                                    '{}'),
        (['http://host-1'],                     '{"url-list": "http://host-1"}'),
        (['http://host-1', 'http://host-2'],    '{"url-list": ["http://host-1", "http://host-2"]}'),
    )
    def test_url_list_outputs_list_or_single_or_none(self, value, expected_json):
        raw_bytes = bencode.encode({'url-list': value})
        t = torrent.parse(raw_bytes)

        with temp_file_path(suffix='.json') as file_path:
            self.assertFalse(path.exists(file_path))

            t.dump(file_path)
            self.assertIsNone(t.file_path)
            self.assertTrue(path.exists(file_path))
            self.assertEqual(read_str(file_path), expected_json)

    @tcm.values(
        ([],                '{}'),
        ([['host', 8080]],  '{"nodes": [["host", 8080]]}'),
    )
    def test_node_list_outputs_list_or_none(self, value, expected_json):
        raw_bytes = bencode.encode({'nodes': value})
        t = torrent.parse(raw_bytes)

        with temp_file_path(suffix='.json') as file_path:
            self.assertFalse(path.exists(file_path))

            t.dump(file_path)
            self.assertIsNone(t.file_path)
            self.assertTrue(path.exists(file_path))
            self.assertEqual(read_str(file_path), expected_json)

    @tcm.values(
        ([],
            '{}'),

        ([['http://tracker'], ['http://one', 'http://two']],
            '{"announce-list": [["http://tracker"], ["http://one", "http://two"]]}'),
    )
    def test_announce_list_outputs_list_or_none(self, value, expected_json):
        raw_bytes = bencode.encode({'announce-list': value})
        t = torrent.parse(raw_bytes)

        with temp_file_path(suffix='.json') as file_path:
            self.assertFalse(path.exists(file_path))

            t.dump(file_path)
            self.assertIsNone(t.file_path)
            self.assertTrue(path.exists(file_path))
            self.assertEqual(read_str(file_path), expected_json)

    def test_unexpected_types_will_raise(self):
        t = torrent.new()
        t.data['x'] = self

        with temp_file_path(suffix='.json') as file_path:
            with self.assertRaises(TypeError) as outcome:
                t.dump(file_path)
            message = outcome.exception.args[0]
            self.assertIn('not JSON serializable', message)


@contextmanager
def temp_file_path(*, suffix='.torrent', contents=None):
    with NamedTemporaryFile(prefix='clot-', suffix=suffix, delete=contents is None) as file:
        if contents is not None:
            file.write(contents)
        file_path = file.name

    try:
        yield file_path
    finally:
        remove(file_path)


def read_bytes(file_path):
    with open(file_path, 'rb') as file:
        return file.read()


def read_str(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()
