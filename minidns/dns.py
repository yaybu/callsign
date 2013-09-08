from zope.interface import implements

from twisted.application import service, internet, strports
from twisted.names.server import DNSServerFactory
from twisted.names.client import createResolver
from twisted.names.authority import FileAuthority
from twisted.names.common import ResolverBase
from twisted.names.dns import DNSDatagramProtocol, Record_A, Record_SOA

class RuntimeAuthority(FileAuthority):

    def __init__(self, domain):
        ResolverBase.__init__(self)
        self._cache = {}
        self.records = {}
        self.soa = (domain, Record_SOA(
            mname='localhost',
            rname='root.localhost',
            serial=1,
            refresh="1H",
            retry="1H",
            expire="1H",
            minimum="1"
        ))
        self.records[domain] = [self.soa[1]]

    def set_record(self, name, value):
        print "Setting", name, "=", value
        self.records["%s.%s" % (name, self.soa[0])] = [Record_A(address=value)]

    def a_records(self):
        for k,v in self.records.items():
            if isinstance(v, Record_A):
                yield (k.rtrim(self.soa[0]), v.address)

class DNSService(service.MultiService):

    implements(service.IServiceCollection)

    def __init__(self, config):
        service.MultiService.__init__(self)
        self.authority = RuntimeAuthority(config.domain)
        self.resolver = createResolver(servers=[('8.8.8.8', 53), ('8.8.4.4', 53)])
        self.factory = DNSServerFactory(authorities=[self.authority], clients=[self.resolver])
        self.protocol = DNSDatagramProtocol(self.factory)
        self.udpservice = internet.UDPServer(config.udp_port, self.protocol)
        self.tcpservice = internet.TCPServer(config.tcp_port, self.factory)
        self.services = [
            self.udpservice,
            self.tcpservice,
            ]

    def set_record(self, name, value):
        self.authority.set_record(name, value)

    def get_records(self):
        return self.authority.a_records()
