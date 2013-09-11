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
from twisted.application import internet
from twisted.web.server import Site
from twisted.web.resource import Resource, NoResource
import socket

class RecordResource(Resource):

    err_invalid_body = 'Request body should be of the form "TYPE DATA"'
    err_wrong_record_type = "Only A type records are supported"
    err_malformed = "Malformed IP Address"

    def __init__(self, name, zone):
        Resource.__init__(self)
        self.name = name
        self.zone = zone

    def render_PUT(self, request):
        data = request.content.read()
        try:
            type_, ip = data.split()
        except ValueError:
            request.setResponseCode(400, message=self.err_invalid_body)
            return ""
        if type_ != 'A':
            request.setResponseCode(400, message=self.err_wrong_record_type)
            return ""
        try:
            self.zone.set_record(self.name, ip)
        except socket.error:
            request.setResponseCode(400, message=self.err_malformed)
            return ""
        request.setResponseCode(201)
        return ""

    def render_DELETE(self, request):
        try:
            self.zone.delete_record(self.name)
        except KeyError:
            request.setResponseCode(404)
            return ""
        request.setResponseCode(204)
        return ""

    def render_GET(self, request):
        type_, ip = self.zone.get_record(self.name)
        return "%s %s" % (type_, ip)

class DomainResource(Resource):

    def __init__(self, zone, dnsserver):
        Resource.__init__(self)
        self.zone = zone
        self.dnsserver = dnsserver

    def render_GET(self, request):
        l = []
        for type_, name, value in self.zone.a_records():
            l.append("%s %s %s" % (type_, name, value))
        return "\n".join(l)

    def render_DELETE(self, request):
        self.dnsserver.delete_zone(self.zone.soa[0])
        request.setResponseCode(204)
        return ""

    def render_PUT(self, request):
        request.setResponseCode(200)
        return ""

    def getChild(self, path, request):
        return RecordResource(path, self.zone)

class MissingDomainResource(Resource):

    """ A resource that can only be PUT to to create a new zone """

    def __init__(self, name, factory):
        Resource.__init__(self)
        self.name = name
        self.factory = factory

    def render_PUT(self, request):
        self.factory.add_zone(self.name)
        request.setResponseCode(201)
        return ""

    def render_GET(self, request):
        request.setResponseCode(404)
        return ""

    def render_HEAD(self, request):
        request.setResponseCode(404)
        return ""

    def render_DELETE(self, request):
        request.setResponseCode(404)
        return ""

class RootResource(Resource):

    def __init__(self, config, dnsserver):
        Resource.__init__(self)
        self.config = config
        self.dnsserver = dnsserver

    def render_GET(self, request):
        return "\n".join(self.dnsserver.zones())

    def getChild(self, path, request):
        if path == "":
            return self
        path = path.rstrip(".")
        try:
            zone = self.dnsserver.get_zone(path)
            return DomainResource(zone, self.dnsserver)
        except KeyError:
            return MissingDomainResource(path, self.dnsserver.factory)

class MiniDNSSite(Site):

    def log(self, *a, **kw):
        pass

def webservice(config, dnsserver):
    root = RootResource(config, dnsserver)
    site = MiniDNSSite(root)
    return internet.TCPServer(config['www_port'], site)
