from contextlib import contextmanager
from os import path, remove
from tempfile import NamedTemporaryFile

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
            self.assertEqual(read_from(file_path), t.raw_bytes)

    def test_existing_file_will_raise_by_default(self):
        t = torrent.new()
        t.data['my'] = 'value'

        with temp_file_path(contents=b'old garbage') as file_path:
            self.assertTrue(path.exists(file_path))
            self.assertEqual(read_from(file_path), b'old garbage')

            with self.assertRaises(FileExistsError):
                t.save_as(file_path)
            self.assertEqual(t.raw_bytes, b'de')
            self.assertIsNone(t.file_path)
            self.assertEqual(read_from(file_path), b'old garbage')

    def test_existing_file_can_be_overwritten_when_asked(self):
        t = torrent.new()
        t.data['my'] = 'value'

        with temp_file_path(contents=b'old garbage') as file_path:
            self.assertTrue(path.exists(file_path))
            self.assertEqual(read_from(file_path), b'old garbage')

            t.save_as(file_path, overwrite=True)
            self.assertEqual(t.raw_bytes, b'd2:my5:valuee')
            self.assertEqual(t.file_path, file_path)
            self.assertEqual(read_from(file_path), t.raw_bytes)


@contextmanager
def temp_file_path(*, contents=None):
    with NamedTemporaryFile(prefix='clot-', suffix='.torrent', delete=contents is None) as file:
        if contents is not None:
            file.write(contents)
        file_path = file.name

    try:
        yield file_path
    finally:
        remove(file_path)


def read_from(file_path):
    with open(file_path, 'rb') as file:
        return file.read()
