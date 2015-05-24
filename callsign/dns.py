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

from twisted.application import service, internet
from twisted.names.server import DNSServerFactory
from twisted.names.client import createResolver
from twisted.names.authority import FileAuthority
from twisted.names.common import ResolverBase
from twisted.names.resolve import ResolverChain
from twisted.names.dns import DNSDatagramProtocol, Record_SOA
from twisted.python import log

from itertools import chain
import os
import json
import pwd

from twisted.python.util import switchUID

import mapper


def _getsubdomain(name, domain):
    domlen = len(domain)
    if name[-domlen:] == domain:
        return name[:-domlen].rstrip('.')
    return name


# Need to cope with default TTL - seems to be an issue when not set
def _is_record_valid(name, irecord, rec_list):
    # maybe do other sanity checking here
    if not rec_list:
        return (True, "New hostname")
    type_ = mapper.get_typestring(irecord)
    # if current rec is CNAME or NS check for root name
    if not name and type_ in ('CNAME', 'NS'):
        return (False, "Root hostname not allowed in this zone")
    # if current rec is CNAME, can't clash
    if rec_list and type_ == 'CNAME':
        return (False, "CNAME can't use existing hostname")
    # check for existing CNAME
    sub_rec_list = [rec for rec in rec_list if mapper.get_typestring(rec) == 'CNAME']
    if sub_rec_list:
        return (False, "CNAME already exists with this hostname")
    match_rec_list = [rec for rec in rec_list if rec.TYPE == irecord.TYPE]
    # if matching records of same type, check TTL
    if match_rec_list and match_rec_list[0].ttl != irecord.ttl:
        return (False, "TTL is different from existing entry for this hostname")
    log.msg("checking for uniqueness")
    # if hostname matches, check that unique attrs differ
    for rec in match_rec_list:
        match_attr = mapper.unique_attr_map[type_]
        if getattr(rec, match_attr) == getattr(irecord, match_attr):
            return (False, "%s already exists for this host with same information" % type_)
    return (True, "OK")


class RuntimeAuthority(FileAuthority):

    def check_type(self, type_):
        return type_ in mapper.record_types

    def __init__(self, domain, savedir=None):
        self.savefile = None if savedir is None else os.path.join(savedir, domain)
        ResolverBase.__init__(self)
        self._cache = {}
        self.records = {}
        self.domain = domain
        self.load()
        self.create_soa()

    def save(self):
        if self.savefile is None:
            return
        # needs to be list, as can have multiple As for same host/sub, e.g.
        data = []
        # record type encodes itself as in mapper
        for name, rec_items in self.records.items():
            name = _getsubdomain(name, self.domain.lower())
            for irecord in rec_items:
                type_ = mapper.get_typestring(irecord)
                values = mapper.get_attrs(irecord)
                values['type'] = type_
                if values:
                    data.append({name: values})
        # only save if data exists
        if data:
            f = open(self.savefile + ".tmp", "w")
            json.dump(data, f)
            f.close()
            os.rename(self.savefile + ".tmp", self.savefile)

    def load(self):
        if self.savefile is None:
            return
        if os.path.exists(self.savefile):
            try:
                # set dirty flag and re-save if invalid data in save file
                dirty = False
                data = json.load(open(self.savefile))
                for item in data:
                    name, rec = item.items()[0]
                    type_ = rec.pop('type')
                    if name and rec:
                        (success, msg) = self.set_record(name, type_, rec, False)
                        log.msg(msg)
                        if not success:
                            dirty = True
                if dirty:
                    self.save()
            except ValueError:
                log.msg("No JSON in save file")

    def create_soa(self):
        # Maybe allow these to be changed?
        soa_rec = Record_SOA(
            mname='localhost',
            rname='root.localhost',
            serial=1,
            refresh="1H",
            retry="1H",
            expire="1H",
            minimum="1"
        )
        self.soa = [self.domain.lower(), soa_rec]

    def set_record(self, name, type_, values, do_save):
        if type_ in mapper.record_types:
            # twisted str2time does not like u-strings
            if 'ttl' in values:
                if values['ttl'] == 'None':
                    values.pop('ttl')
                else:
                    values['ttl'] = values['ttl'].encode('utf-8')

            log.msg("Setting %s = %s" % (name, values))

            # have to special case data type for txt records, grrr
            if 'data' in values:
                data = values.pop('data')
                irecord = mapper.record_types[type_](*data, **values)
            else:
                irecord = mapper.record_types[type_](**values)

            full_name = ("%s.%s" % (name, self.domain)).lower()
            log.msg("testing validity")
            (is_valid, status) = _is_record_valid(name, irecord, self.records.get(full_name, []))

            log.msg(status)

            if is_valid:
                self.records.setdefault(full_name, []).append(irecord)
                if do_save:
                    self.save()
                return (True, "Record Added")
            else:
                log.msg("Constraint invalidated")
                return (False, status)
        else:
            log.msg("Invalid record type: %s" % type_)
            return (False, "Record not supported")

    def get_record_details(self, name, record):
        details = (mapper.get_typestring(record),
                   name,
                   mapper.get_values(record)
                   )
        log.msg("Retreived Record: %s %s %s" % details)
        return details

    """
    Convenience method for display of all records
    """
    def allrecords(self):
        data = []
        for name_rec in self.records.items():
            for r in name_rec[1]:
                data.append(self.get_record_details(name_rec[0], r))
        return data

    def get_records_by_name(self, name):
        data = []
        fullname = "%s.%s" % (name, self.domain)
        if fullname in self.records:
            for r in self.records[fullname]:
                data.append(self.get_record_details(fullname, r))
        return data

    def get_records_by_type(self, type_):
        data = []
        for k, v in self.records.items():
            data.extend([self.get_record_details(k, item) for item in v if mapper.get_typestring(item) == type_])
        return data

    def delete_record(self, name):
        del self.records["%s.%s" % (name, self.domain)]
        self.save()


class CallsignResolverChain(ResolverChain):

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
        if name in self.authorities:
            # do we want to nuke save zone info at this point?
            savefile = self.authorities[name].savefile
            if savefile and os.path.exists(savefile):
                os.remove(savefile)
            del self.authorities[name]

    def add_zone(self, name):
        if name not in self.authorities:
            print "Creating zone", name
            self.authorities[name] = RuntimeAuthority(name, self.savedir)
        else:
            print "Not clobbering existing zone"

    def zones(self):
        return self.authorities.keys()


class CallsignServerFactory(DNSServerFactory):

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
        self.resolver = CallsignResolverChain([forward_resolver], self.savedir)
        self.verbose = True
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
        self.factory = CallsignServerFactory(forwarders, savedir, self.get_ent())
        self.protocol = DNSDatagramProtocol(self.factory)

    def get_zone(self, name):
        return self.factory.get_zone(name)

    def delete_zone(self, name):
        return self.factory.delete_zone(name)

    def zones(self):
        return self.factory.zones()

    def startService(self):
        udpservice = internet.UDPServer(self.port, self.protocol, interface="127.0.0.1")
        udpservice.startService()
        log.msg("Nameserver listening on port %d" % self.port)
        self.services.append(udpservice)
        self.drop_privileges()

    def get_ent(self):
        ent = pwd.getpwnam(self.conf['user'])
        return ent

    def drop_privileges(self):
        ent = pwd.getpwnam(self.conf['user'])
        switchUID(ent.pw_uid, ent.pw_gid)

    def stopService(self):
        service.MultiService.stopService(self)
