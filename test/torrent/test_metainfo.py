import tcm

from clot import bencode, torrent


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

    def test_mapping_is_parsed_into_correct_fields(self):
        raw_bytes = bencode.encode({
            'info': {},
            'announce': 'http://tracker/announce',
            'announce-list': [['tracker'], ['backup1'], ['backup2']],
            'creation date': 0,
            'comment': 'a trivial comment',
            'created by': 'clot/0.0.0',
            'encoding': 'UTF-8',

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
