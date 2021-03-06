import tcm

from clot import bencode, torrent


LETTER_BE = '\N{CYRILLIC CAPITAL LETTER BE}'


class CreateTestCase(tcm.TestCase):
    def test_new_torrent_has_none_in_all_fields(self):
        t = torrent.new()

        self.assertDictEqual(t.data, {})
        self.assertIsNone(t.file_path)

        self.assertIsNone(t.info)
        self.assertIsNone(t.announce)
        self.assertIsNone(t.announce_list)
        self.assertIsNone(t.creation_date)
        self.assertIsNone(t.comment)
        self.assertIsNone(t.created_by)
        self.assertIsNone(t.encoding)
        self.assertIsNone(t.publisher)
        self.assertIsNone(t.publisher_url)
        self.assertIsNone(t.nodes)
        self.assertIsNone(t.url_list)
        self.assertIsNone(t.private)
        self.assertIsNone(t.codepage)

    def test_mapping_is_parsed_into_correct_fields(self):
        raw_bytes = bencode.encode({
            'info': {},
            'announce': 'http://tracker/announce',
            'announce-list': [['tracker'], ['backup1'], ['backup2']],
            'creation date': 0,
            'comment': 'a trivial comment',
            'created by': 'clot/0.0.0',
            'encoding': 'UTF-8',
            'publisher': 'torrent creator',
            'publisher-url': 'http://creator.site/and/path',
            'nodes': [['host-a', 123], ['host-b', 456]],
            'url-list': ['http://mirror.com/pub', 'http://another.com/pub'],
            'private': 1,
            'codepage': 437,

            'unknown to clot': 'stays in data dict',
        })

        t = torrent.parse(raw_bytes)

        self.assertDictEqual(t.data, {'unknown to clot': b'stays in data dict'})
        self.assertIsNone(t.file_path)

        self.assertDictEqual(t.info, {})
        self.assertEqual(t.announce, 'http://tracker/announce')
        self.assertListEqual(t.announce_list, [[b'tracker'], [b'backup1'], [b'backup2']])
        self.assertEqual(t.creation_date.isoformat(), '1970-01-01T00:00:00+00:00')
        self.assertEqual(t.comment, 'a trivial comment')
        self.assertEqual(t.created_by, 'clot/0.0.0')
        self.assertEqual(t.encoding, 'UTF-8')
        self.assertEqual(t.publisher, 'torrent creator')
        self.assertEqual(t.publisher_url, 'http://creator.site/and/path')
        self.assertListEqual(t.nodes, [[b'host-a', 123], [b'host-b', 456]])
        self.assertEqual(t.url_list, [b'http://mirror.com/pub', b'http://another.com/pub'])
        self.assertEqual(t.private, 1)
        self.assertEqual(t.codepage, 437)

    def test_fields_can_be_lazy_loaded(self):
        raw_bytes = bencode.encode({
            'comment': 'a trivial comment',
        })

        t = torrent.parse(raw_bytes, lazy=True)

        self.assertDictEqual(t.data, {'comment': b'a trivial comment'})
        self.assertFalse(hasattr(t, '_comment'))
        self.assertEqual(t.comment, 'a trivial comment')
        self.assertTrue(hasattr(t, '_comment'))

    def test_fallback_encoding_is_used(self):
        t = torrent.new()

        t.data['comment'] = LETTER_BE.encode('cp1251')

        self.assertIsNone(t.fallback_encoding)
        with self.assertRaises(ValueError) as outcome:
            t.load_fields()     # pylint: disable=no-member
        message = outcome.exception.args[0]
        self.assertEqual(message, r"comment: cannot decode b'\xc1' as UTF-8")

        t.fallback_encoding = 'cp1251'
        t.load_fields()         # pylint: disable=no-member
        self.assertEqual(t.comment, LETTER_BE)
