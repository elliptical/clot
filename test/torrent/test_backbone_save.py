from contextlib import contextmanager
from os import path, remove
from tempfile import NamedTemporaryFile
import textwrap

import tcm

from clot import torrent


class SaveAsTestCase(tcm.TestCase):
    def test_new_file_is_created(self):
        t = torrent.new()
        t.data['my'] = 'value'

        with temp_file_path() as file_path:
            self.assertFalse(path.exists(file_path))

            t.save_as(file_path)
            self.assertEqual(t.raw_bytes, b'd2:my5:valuee')
            self.assertEqual(t.file_path, file_path)
            self.assertTrue(path.exists(file_path))
            self.assertEqual(read_bytes(file_path), t.raw_bytes)

    def test_existing_file_will_raise_by_default(self):
        t = torrent.new()
        t.data['my'] = 'value'

        with temp_file_path(contents=b'old garbage') as file_path:
            self.assertTrue(path.exists(file_path))
            self.assertEqual(read_bytes(file_path), b'old garbage')

            with self.assertRaises(FileExistsError):
                t.save_as(file_path)
            self.assertEqual(t.raw_bytes, b'de')
            self.assertIsNone(t.file_path)
            self.assertEqual(read_bytes(file_path), b'old garbage')

    def test_existing_file_can_be_overwritten_when_asked(self):
        t = torrent.new()
        t.data['my'] = 'value'

        with temp_file_path(contents=b'old garbage') as file_path:
            self.assertTrue(path.exists(file_path))
            self.assertEqual(read_bytes(file_path), b'old garbage')

            t.save_as(file_path, overwrite=True)
            self.assertEqual(t.raw_bytes, b'd2:my5:valuee')
            self.assertEqual(t.file_path, file_path)
            self.assertEqual(read_bytes(file_path), t.raw_bytes)


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
            self.assertEqual(t.raw_bytes, b'd2:my8:modifiede')
            self.assertEqual(read_bytes(file_path), t.raw_bytes)

    def test_loaded_file_can_be_saved_elsewhere(self):
        with temp_file_path(contents=b'd2:my5:valuee') as file_path:
            t = torrent.load(file_path)
            t.data['my'] = 'modified'

            with temp_file_path() as new_file_path:
                t.save_as(new_file_path)
                self.assertEqual(t.raw_bytes, b'd2:my8:modifiede')
                self.assertEqual(t.file_path, new_file_path)
                self.assertEqual(read_bytes(new_file_path), t.raw_bytes)

            self.assertEqual(read_bytes(file_path), b'd2:my5:valuee')


class DumpTestCase(tcm.TestCase):
    def test_existing_file_will_raise_by_default(self):
        t = torrent.new()

        with temp_file_path(contents=b'old garbage') as file_path:
            self.assertTrue(path.exists(file_path))
            self.assertEqual(read_bytes(file_path), b'old garbage')

            with self.assertRaises(FileExistsError):
                t.dump(file_path)
            self.assertEqual(read_bytes(file_path), b'old garbage')

    def test_existing_file_can_be_overwritten_when_asked(self):
        t = torrent.new()

        with temp_file_path(contents=b'old garbage') as file_path:
            self.assertTrue(path.exists(file_path))
            self.assertEqual(read_bytes(file_path), b'old garbage')

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
            self.assertEqual(t.raw_bytes, b'de')
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
            self.assertEqual(t.raw_bytes, b'de')
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
            self.assertEqual(t.raw_bytes, b'de')
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
