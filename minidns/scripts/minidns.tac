from twisted.application import service

from minidns.dns import DNSService
from minidns.restapi import webservice

import os
import ConfigParser

class ConfigProxy:
    """ ConfigParser API is horrid. So is this. """
    def __init__(self, config_parser):
        self.cp = config_parser

    def __getattr__(self, name):
        v = self.cp.get("minidns", name)
        try:
            return int(v)
        except ValueError:
            return v

config_file = os.environ["MINIDNS_CONFIG_FILE"]

cp = ConfigParser.ConfigParser()
if not os.path.exists(config_file):
    raise IOError("Config file %r does not exist" % config_file)
cp.read(config_file)

config = ConfigProxy(cp)

application = service.Application("minidns")

dnsserver = DNSService(config)
dnsserver.setServiceParent(application)

webserver = webservice(config, dnsserver)
webserver.setServiceParent(application)

