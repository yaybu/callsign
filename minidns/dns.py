from zope.interface import implements

from twisted.application import service, internet, strports
from twisted.names.server import DNSServerFactory
from twisted.names.client import createResolver
from twisted.names.dns import DNSDatagramProtocol

class DNSService(service.MultiService):

    implements(service.IServiceCollection)

    def __init__(self, config):
        service.MultiService.__init__(self)
        self.resolver = createResolver()
        self.factory = DNSServerFactory(None, clients=[self.resolver])
        self.protocol = DNSDatagramProtocol(self.factory)
        self.udpservice = internet.UDPServer(config.udp_port, self.protocol)
        self.tcpservice = internet.TCPServer(config.tcp_port, self.factory)
        self.services = [
            self.udpservice,
            self.tcpservice,
            ]

