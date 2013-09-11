from twisted.trial import unittest
from minidns.dns import RuntimeAuthority, MiniDNSResolverChain, Record_A
from mock import MagicMock, patch

class TestRuntimeAuthority(unittest.TestCase):

    def setUp(self):
        self.a = RuntimeAuthority("foo")

    def test_a_records(self):
        foo_value = MagicMock(Record_A)
        bar_value = MagicMock(Record_A)
        foo_value.dottedQuad.return_value = "192.168.0.1"
        bar_value.dottedQuad.return_value = "192.168.0.2"
        self.a.records = {
            "foo.foo": [foo_value],
            "bar.foo": [bar_value],
            }
        rv = self.a.a_records()
        self.assertEqual(sorted(rv), [
            ("A", "bar", "192.168.0.2"),
            ("A", "foo", "192.168.0.1"),
            ])

