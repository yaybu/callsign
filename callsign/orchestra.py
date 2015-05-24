
from twisted.application import service

from .dns import DNSService
from .restapi import webservice


class OrchestrationService(service.MultiService):

    """ Handles starting and stopping. """

    def __init__(self, conf):
        service.MultiService.__init__(self)
        self.conf = conf
        self.dnsserver = DNSService(conf)
        self.dnsserver.setServiceParent(self)
        self.webserver = webservice(conf, self.dnsserver)
        self.webserver.setServiceParent(self)
