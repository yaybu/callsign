from zope.interface import implements

from twisted.application import service, internet, strports
from twisted.names.server import DNSServerFactory
from twisted.names.client import createResolver
from twisted.names.dns import DNSDatagramProtocol, Record_A, Record_SOA

def soa(domain):
        return Record_SOA(
            mname='localhost',
            rname='root.localhost',
            serial=1,
            refresh="1H",
            retry="1H",
            expire="1H",
            minimum="1"
            )


class DNSService(service.MultiService):

    implements(service.IServiceCollection)

    def __init__(self, config):
        self.zones = {}
        self.zones[config.domain] = []
        self.zones[config.domain].append(soa(config.domain))
        service.MultiService.__init__(self)
        self.resolver = createResolver()
        self.factory = DNSServerFactory(self.zones, clients=[self.resolver])
        self.protocol = DNSDatagramProtocol(self.factory)
        self.udpservice = internet.UDPServer(config.udp_port, self.protocol)
        self.tcpservice = internet.TCPServer(config.tcp_port, self.factory)
        self.services = [
            self.udpservice,
            self.tcpservice,
            ]

    def set_record(self, name, value):
        open("/tmp/foo", "w").write("%s %s" % (name, value))

