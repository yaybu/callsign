from twisted.application import service

from minidns.dns import DNSService
from minidns.restapi import webservice
from minidns.config import config

import os

config_file = os.environ.get("MINIDNS_CONFIG_FILE", None)
conf = config(config_file)

application = service.Application("minidns")

dnsserver = DNSService(conf)
dnsserver.setServiceParent(application)

webserver = webservice(conf, dnsserver)
webserver.setServiceParent(application)

