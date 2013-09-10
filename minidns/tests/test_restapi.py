from twisted.trial import unittest
from mock import MagicMock
from minidns.restapi import RootResource, DomainResource, RecordResource, MissingDomainResource

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
        self.assertEqual(rv, "\n".join(["%s %s %s" % (x,y,z) for (x,y,z) in data]))

class TestMissingDomainResource(unittest.TestCase):
    pass


