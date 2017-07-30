import tcm

from bencode import decoder


class TestCase(tcm.TestCase):
    def test_module_docstring_is_present(self):
        self.assertIsNotNone(decoder.__doc__)
