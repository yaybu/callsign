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

import os
import json

from twisted.trial import unittest
from callsign.dns import RuntimeAuthority, Record_A
from mock import MagicMock


class TestRuntimeAuthority(unittest.TestCase):

    def setUp(self):
        self.a = RuntimeAuthority("foo", None)

    def test_a_records(self):
        foo_value = MagicMock(Record_A, autospec=True)
        bar_value = MagicMock(Record_A, autospec=True)
        foo_value.TYPE = 1
        bar_value.TYPE = 1
        foo_value.name = "foo"
        bar_value.name = "bar"
        foo_value.ttl = None
        bar_value.ttl = None
        foo_value.compareAttributes = ('address', 'ttl')
        bar_value.compareAttributes = ('address', 'ttl')
        foo_value.dottedQuad.return_value = "192.168.0.1"
        bar_value.dottedQuad.return_value = "192.168.0.2"
        self.a.records = {
            "foo.foo": [foo_value],
            "bar.foo": [bar_value],
        }
        rv = self.a.get_records_by_type("A")
        self.assertEqual(sorted(rv), [
            ("A", "bar.foo", ["192.168.0.2"]),
            ("A", "foo.foo", ["192.168.0.1"]),
        ])

    def test_txt_records(self):
        pass

    def test_cname_records(self):
        pass

    def test_conflict_rules(self):
        pass

    def test_load(self):
        os.mkdir("savedir")
        json.dump((
            {"bar": {
                "type": "A",
                "address": "192.168.1.1",
            }},
            {"baz": {
                "type": "A",
                "address": "192.168.1.2",
            }},
        ), open("savedir/foo", "w"))
        self.a = RuntimeAuthority("foo", "savedir")
        self.assertEqual(self.a.records, {
            "bar.foo": [Record_A(address="192.168.1.1")],
            "baz.foo": [Record_A(address="192.168.1.2")],
        })
        os.unlink("savedir/foo")
        os.rmdir("savedir")

    def test_save(self):
        os.mkdir("savedir")
        self.a = RuntimeAuthority("foo", "savedir")
        self.a.set_record("baz", "A", {'address': "192.168.1.2"}, True)
        self.a.set_record("bar", "A", {'address': "192.168.1.1"}, True)
        self.assertEqual(json.load(open("savedir/foo")), [
            {"bar": {
                "type": "A",
                "address": "192.168.1.1",
            }},
            {"baz": {
                "type": "A",
                "address": "192.168.1.2",
            }}
        ])
