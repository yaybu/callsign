#Copyright 2013 Isotoma Limited
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

from zope.interface import implements

from twisted.application import service, internet, strports
from twisted.names.server import DNSServerFactory
from twisted.names.client import createResolver
from twisted.names.authority import FileAuthority
from twisted.names.common import ResolverBase
from twisted.names.resolve import ResolverChain
from twisted.names.dns import DNSDatagramProtocol, Record_A, Record_SOA
from twisted.python import log
from twisted.internet.error import CannotListenError

from itertools import chain
import os
import sys
import json
import subprocess
import shlex
import pwd
from twisted.python.util import switchUID

class RuntimeAuthority(FileAuthority):

    def __init__(self, domain, savedir=None):
        self.savefile = None if savedir is None else os.path.join(savedir, domain)
        ResolverBase.__init__(self)
        self._cache = {}
        self.records = {}
        self.domain = domain
        # TODO: deal with SOA record?
        self.load()
        if not self.records:
            self.save()
        self.create_soa()

    def save(self):
        if self.savefile is None: return
        data = {}
        # Maybe have each record type encode itself
        for name, value in self.records.items():
            if isinstance(value[0], Record_A):
                data[name.rstrip("."+self.domain)] = {
                    'type': 'A',
                    'value': value[0].dottedQuad(),
                    }

        f = open(self.savefile + ".tmp", "w")
        json.dump(data, f)
        f.close()
        os.rename(self.savefile + ".tmp", self.savefile)

    def load(self):
        if self.savefile is None: return
        if os.path.exists(self.savefile):
            data = json.load(open(self.savefile))
            for name, value in data.items():
                if value['type'] == 'A':
                    self.set_record(name, value['value'])

    def create_soa(self):
        soa_rec = Record_SOA(
            mname='localhost',
            rname='root.localhost',
            serial=1,
            refresh="1H",
            retry="1H",
            expire="1H",
            minimum="1"
        )
        # self.records[self.domain] = [soa]
        # trying a nicer way - then doesn't matter if record has items
        self.records.setdefault(self.domain.lower(), []).insert(0, soa_rec)
        
        # need this for super
        self.soa=[self.domain.lower(), soa_rec]

    def set_record(self, name, value):
        print "Setting", name, "=", value
        self.records["%s.%s" % (name, self.domain)] = [Record_A(address=value)]
        self.save()

    def get_record(self, name):
        r = self.records["%s.%s" % (name, self.domain)][0]
        if isinstance(r, Record_A):
            return ('A', r.dottedQuad())

    def delete_record(self, name):
        del self.records["%s.%s" % (name, self.domain)]
        self.save()

    def a_records(self):
        for k,v in self.records.items():
            v = v[0]
            if isinstance(v, Record_A):
                yield ('A', k.rstrip(self.domain).rstrip("."), v.dottedQuad())

class MiniDNSResolverChain(ResolverChain):

    def __init__(self, defaults, savedir):
        ResolverBase.__init__(self)
        self.defaults = defaults
        self.authorities = {}
        self.savedir = savedir

    @property
    def resolvers(self):
        return list(chain(self.authorities.values(), self.defaults))

    def get_zone(self, name):
        return self.authorities[name]

    def delete_zone(self, name):
        print "Deleting zone", name
        del self.authorities[name]

    def add_zone(self, name):
        if name not in self.authorities:
            print "Creating zone", name
            self.authorities[name] = RuntimeAuthority(name, self.savedir)
        else:
            print "Not clobbering existing zone"

    def zones(self):
        return self.authorities.keys()

class MiniDNSServerFactory(DNSServerFactory):

    def __init__(self, forwarders, savedir, ent):
        self.canRecurse = True
        self.connections = []
        self.forwarders = forwarders
        forward_resolver = createResolver(servers=[(x, 53) for x in forwarders])
        self.savedir = savedir
        if self.savedir is not None:
            self.savedir = os.path.expanduser(self.savedir)
            if not os.path.exists(self.savedir):
                log.msg("Setting up save directory " + savedir)
                os.mkdir(self.savedir)
                os.chown(self.savedir, ent.pw_uid, ent.pw_gid)
        self.resolver = MiniDNSResolverChain([forward_resolver], self.savedir)
        self.verbose = False
        self.load() 

    def doStart(self):
        if not self.numPorts:
            log.msg("Starting DNS Server using these forwarders: %s" % (",".join(self.forwarders)))
        self.numPorts = self.numPorts + 1
        self.load()

    def load(self):
        for f in os.listdir(self.savedir):
            self.add_zone(f)

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

    def __init__(self, conf):
        service.MultiService.__init__(self)
        self.conf = conf
        forwarders = self.conf['forwarders'].split()
        savedir = self.conf['savedir']
        self.port = self.conf['udp_port']        
        self.authorities = []
        self.factory = MiniDNSServerFactory(forwarders, savedir, self.get_ent())
        self.protocol = DNSDatagramProtocol(self.factory)

    def get_zone(self, name):
        return self.factory.get_zone(name)

    def delete_zone(self, name):
        return self.factory.delete_zone(name)

    def zones(self):
        return self.factory.zones()

    def startService(self):
        udpservice = internet.UDPServer(53, self.protocol)
        try:
            udpservice.startService()
            log.msg("Nameserver listening on port 53")
        except CannotListenError:
            log.msg("Nameserver cannot bind to port 53, trying %d" % self.port)
            udpservice = internet.UDPServer(self.port, self.protocol)
            udpservice.startService()
            log.msg("Nameserver listening on port %d" % self.port)
            self.port_forward()
        self.services.append(udpservice)
        self.rewrite_and_monitor_resolvconf()
        self.drop_privileges()
       
    def get_ent(self):
        ent = pwd.getpwnam(self.conf['user'])
        return ent      
        
    def drop_privileges(self):
        ent = pwd.getpwnam(self.conf['user'])
        switchUID(ent.pw_uid, ent.pw_gid)
        
    def rewrite_and_monitor_resolvconf(self):
        """ If the only nameserver listed is 127.0.0.1, then we don't need to
        rewrite resolv.conf. Otherwise we do some mad stuff. """
        #path = os.path.dirname(sys.argv[0])
        #subprocess.check_output([os.path.join(path, "resolvmgr"), str(os.getpid())])

    def stopService(self):
        service.MultiService.stopService(self)

    def port_forward(self):
        cmd = self.conf["port-forward"].format(port=self.conf['udp_port'])
        rv = subprocess.call(shlex.split(cmd))
        if rv != 0:
            raise SystemExit("failed to execute %r" % cmd)

    def port_unforward(self):
        cmd = self.conf["port-unforward"].format(port=self.conf['udp_port'])
        rv = subprocess.call(shlex.split(cmd))
        if rv != 0:
            raise SystemExit("failed to execute %r" % cmd)

