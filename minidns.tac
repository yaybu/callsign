from twisted.application import service

from minidns.dns import DNSService
from minidns.restapi import webservice

class Config:
    udp_port = 5053
    tcp_port = 5053
    www_port = 5080

application = service.Application("minidns")

dnsserver = DNSService(Config)
dnsserver.setServiceParent(application)

webserver = webservice(Config, dnsserver)
webserver.setServiceParent(application)

