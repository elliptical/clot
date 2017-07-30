import tcm

from bencode import encoder


class TestCase(tcm.TestCase):
    def test_module_docstring_is_present(self):
        self.assertIsNotNone(encoder.__doc__)
