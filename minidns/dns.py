from zope.interface import implements

from twisted.application import service, internet, strports
from twisted.names.server import DNSServerFactory
from twisted.names.client import createResolver
from twisted.names.authority import FileAuthority
from twisted.names.common import ResolverBase
from twisted.names.resolve import ResolverChain
from twisted.names.dns import DNSDatagramProtocol, Record_A, Record_SOA

from itertools import chain

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
        import wingdbstub
        print "Setting", name, "=", value
        self.records["%s.%s" % (name, self.soa[0])] = [Record_A(address=value)]

    def get_record(self, name):
        r = self.records["%s.%s" % (name, self.soa[0])][0]
        if isinstance(r, Record_A):
            return ('A', v.dottedQuad())

    def a_records(self):
        import wingdbstub
        for k,v in self.records.items():
            v = v[0]
            if isinstance(v, Record_A):
                yield ('A', k.rstrip(self.soa[0]), v.dottedQuad())

class MiniDNSResolverChain(ResolverChain):

    def __init__(self, defaults):
        ResolverBase.__init__(self)
        self.defaults = defaults
        self.authorities = {}

    @property
    def resolvers(self):
        return list(chain(self.authorities.values(), self.defaults))

    def get_zone(self, name):
        return self.authorities[name]

    def delete_zone(self, name):
        print "Deleting zone", name
        del self.authorities[name]

    def add_zone(self, name):
        print "Creating zone", name
        self.authorities[name] = RuntimeAuthority(name)
        return self.authorities[name]

    def zones(self):
        return self.authorities.keys()

class MiniDNSServerFactory(DNSServerFactory):

    def __init__(self, forwarders):
        self.canRecurse = True
        self.connections = []
        forward_resolver = createResolver(servers=[(x, 53) for x in forwarders])
        self.resolver = MiniDNSResolverChain([forward_resolver])
        self.verbose = True

    def add_zone(self, name):
        return self.resolver.add_zone(name)

    def delete_zone(self, name):
        return self.resolver.delete_zone(name)

    def get_zone(self, name):
        return self.resolver.get_zone(name)

    def zones(self):
        return self.resolver.zones()

class DNSService(service.MultiService):

    implements(service.IServiceCollection)

    def __init__(self, config):
        service.MultiService.__init__(self)
        self.authorities = []
        self.factory = MiniDNSServerFactory(forwarders=config['forwarders'].split())
        self.protocol = DNSDatagramProtocol(self.factory)
        self.udpservice = internet.UDPServer(config['udp_port'], self.protocol)
        self.tcpservice = internet.TCPServer(config['tcp_port'], self.factory)
        self.services = [
            self.udpservice,
            self.tcpservice,
            ]

    def get_zone(self, name):
        return self.factory.get_zone(name)

    def delete_zone(self, name):
        return self.factory.delete_zone(name)

    def zones(self):
        return self.factory.zones()
