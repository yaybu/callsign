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
from mock import MagicMock
from callsign.restapi import (
    RootResource,
    DomainResource,
    RecordResource,
    MissingDomainResource,
    ForbiddenDomainResource,
)

import socket


class TestRootResource(unittest.TestCase):

    def setUp(self):
        self.config = MagicMock()
        self.dnsserver = MagicMock()
        self.resource = RootResource(self.config, self.dnsserver)

    def test_get(self):
        self.dnsserver.zones = MagicMock(return_value=["foo", "bar"])
        rv = self.resource.render_GET(None)
        self.assertEqual(rv, "\n".join(["foo", "bar"]))

    def test_getChild_exists(self):
        self.config.get = MagicMock(return_value="")
        zone = MagicMock()

        def get_zone(x):
            if x == "foo":
                return zone
            raise KeyError

        self.dnsserver.get_zone.side_effect = get_zone
        rv = self.resource.getChild("foo", None)
        self.assert_(isinstance(rv, DomainResource))
        self.assertEqual(rv.zone, zone)
        rv = self.resource.getChild("bar", None)
        self.assert_(isinstance(rv, MissingDomainResource))
        self.assertEqual(rv.name, "bar")

    def test_getChild_exists_with_lockdown(self):
        self.config.get = MagicMock(return_value="foo bar")
        zone = MagicMock()

        def get_zone(x):
            if x == "foo":
                return zone
            raise KeyError

        self.dnsserver.get_zone.side_effect = get_zone
        rv = self.resource.getChild("foo", None)
        self.assert_(isinstance(rv, DomainResource))
        self.assertEqual(rv.zone, zone)
        rv = self.resource.getChild("bar", None)
        self.assert_(isinstance(rv, MissingDomainResource))
        self.assertEqual(rv.name, "bar")
        rv = self.resource.getChild("baz", None)
        self.assert_(isinstance(rv, ForbiddenDomainResource))


class TestDomainResource(unittest.TestCase):

    def setUp(self):
        self.zone = MagicMock()
        self.dnsserver = MagicMock()
        self.resource = DomainResource(self.zone, self.dnsserver)

    def test_GET(self):
        data = [
            ("A", "www", "192.168.0.1"),
            ("A", "x", "192.168.0.2"),
        ]
        self.zone.a_records = MagicMock(return_value=data)
        rv = self.resource.render_GET(None)
        self.assertEqual(rv, "\n".join(["%s %s %s" % (x, y, z) for (x, y, z) in data]))


class TestMissingDomainResource(unittest.TestCase):

    def setUp(self):
        self.name = "foo"
        self.dnsserver = MagicMock()
        self.resource = MissingDomainResource(self.name, self.dnsserver)

    def test_GET(self):
        request = MagicMock()
        self.resource.render_GET(request)
        request.setResponseCode.assert_called_once_with(404)

    def test_PUT(self):
        request = MagicMock()
        self.resource.render_PUT(request)
        self.dnsserver.add_zone.assert_called_once_with(self.name)
        request.setResponseCode.assert_called_once_with(201)

    def test_HEAD(self):
        request = MagicMock()
        self.resource.render_GET(request)
        request.setResponseCode.assert_called_once_with(404)

    def test_DELETE(self):
        request = MagicMock()
        self.resource.render_GET(request)
        request.setResponseCode.assert_called_once_with(404)


class TestRecordResource(unittest.TestCase):

    def setUp(self):
        self.name = "foo"
        self.zone = MagicMock()
        self.resource = RecordResource(self.name, self.zone)

    def test_PUT(self):
        request = MagicMock()
        request.content.read.return_value = "A 192.168.0.1"
        self.resource.render_PUT(request)
        self.zone.set_record.assert_called_once_with(self.name, "192.168.0.1")
        request.setResponseCode.assert_called_once_with(201)

    def test_PUT_invalid_body(self):
        request = MagicMock()
        request.content.read.return_value = "wrong"
        self.resource.render_PUT(request)
        request.setResponseCode.assert_called_once_with(400, message=self.resource.err_invalid_body)

    def test_PUT_wrong_record_type(self):
        request = MagicMock()
        request.content.read.return_value = "MX 192.168.0.1"
        self.zone.set_record.return_value = (False, "foo")
        self.resource.render_PUT(request)
        request.setResponseCode.assert_called_once_with(400, message=self.resource.err_wrong_record_type)

    def test_PUT_malformed(self):
        request = MagicMock()
        request.content.read.return_value = "A foo"
        self.zone.set_record.side_effect = socket.error()
        self.resource.render_PUT(request)
        request.setResponseCode.assert_called_once_with(400, message=self.resource.err_malformed)

    def test_DELETE(self):
        request = MagicMock()
        self.resource.render_DELETE(request)
        self.zone.delete_record.assert_called_once_with(self.name)
        request.setResponseCode.assert_called_once_with(204)

    def test_DELETE_missing(self):
        request = MagicMock()
        self.zone.delete_record.side_effect = KeyError()
        self.resource.render_DELETE(request)
        self.zone.delete_record.assert_called_once_with(self.name)
        request.setResponseCode.assert_called_once_with(404)

    def test_GET(self):
        self.zone.get_record.return_value = ("A", "192.168.0.1")
        rv = self.resource.render_GET(None)
        self.assertEqual(rv, "A 192.168.0.1")
