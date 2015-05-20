
import os
from twisted.trial import unittest
from minidns.config import get_forwarders

r = """
nameserver 1.1.1.1
nameserver 2.2.2.2
search blah.com
"""

r2 = """
nameserver 127.0.1.1
search blah.com
"""


class TestConfig(unittest.TestCase):

    def test_get_forwarders(self):
        open("resolv.conf", "w").write(r)
        ns = get_forwarders("resolv.conf")
        self.assertEqual(ns, ["1.1.1.1", "2.2.2.2"])
        os.unlink("resolv.conf")

    def test_get_forwarders_not_exists(self):
        self.assertFalse(os.path.exists("resolv.conf"))
        ns = get_forwarders("resolv.conf")
        self.assertEqual(ns, ["8.8.8.8", "8.8.4.4"])

    def test_get_forwarders_no_nameservers(self):
        open("resolv.conf", "w").write("search blah.com\n")
        ns = get_forwarders("resolv.conf")
        self.assertEqual(ns, ["8.8.8.8", "8.8.4.4"])
        os.unlink("resolv.conf")

    def test_get_forwarders_contains_localhost(self):
        open("resolv.conf", "w").write(r2)
        ns = get_forwarders("resolv.conf")
        self.assertEqual(ns, ["8.8.8.8", "8.8.4.4"])
        os.unlink("resolv.conf")
