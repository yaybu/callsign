#Copyright 2013 Isotoma Limited
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

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

