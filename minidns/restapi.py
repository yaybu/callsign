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
from twisted.python import log
import socket
import json

class RecordResource(Resource):

    err_invalid_body = 'Request body should be of the form "TYPE DATA"'
    err_wrong_record_type = "Record type %s is not supported"
    err_malformed = "Malformed IP Address"
    err_invalid_details = "Record data is not valid: %s"

    def __init__(self, name, zone):
        Resource.__init__(self)
        self.name = name
        self.zone = zone

    def render_PUT(self, request):
        try:
            type_ = request.data.pop('type')
        except ValueError, KeyError:
            request.setResponseCode(400, message=self.err_invalid_body)
            return ""
        if not self.zone.check_type(type_):
            msg = self.err_wrong_record_type % type_
            request.setResponseCode(400, message=msg)
            return "" 
        try:
            (success, msg) = self.zone.set_record(self.name, type_, request.data, True)
            if success:
                request.setResponseCode(201)
            else:
                msg = self.err_invalid_details % msg
                request.setResponseCode(400, message=msg)
        except socket.error:
            request.setResponseCode(400, message=self.err_malformed)
            return ""
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
        results = self.zone.get_records_by_name(self.name)
        if not results:
            return "No Records found"
        output = ["%s %s" % (type_, ' '.join(values)) for type_, _name, values in results]
        return "\n".join(output).encode('utf-8')

class DomainResource(Resource):

    def __init__(self, zone, dnsserver):
        Resource.__init__(self)
        self.zone = zone
        self.dnsserver = dnsserver

    def render_GET(self, request):
        results = self.zone.allrecords()
        log.msg('zone results: %s' % results)
        if not results:
            return "No Records found"        
        output = ["%s %s %s" % (type_, name, ' '.join(values)) for type_, name, values in results] 
        return "\n".join(output).encode("utf-8")

    def render_DELETE(self, request):
        self.dnsserver.delete_zone(self.zone.soa[0])
        request.setResponseCode(204)
        return ""

    def render_PUT(self, request):
        raw_data = request.content.read()
        if raw_data == "":
            request.setResponseCode(409, message="Domain already exists, delete first")
            return ""
        try:
            data = json.loads(raw_data)
            name = data.keys()[0]
            values = data.values()[0]
            request.data = values
            resource = self.getChild(name, request)
            return resource.render_PUT(request)
        except ValueError:
            request.setResponseCode(400)

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

class ForbiddenDomainResource(MissingDomainResource):

    def render_PUT(self, request):
        request.setResponseCode(403)
        return ""

class RootResource(Resource):

    def __init__(self, config, dnsserver):
        Resource.__init__(self)
        self.config = config
        self.dnsserver = dnsserver

    def allowed_domain(self, domain):
        if self.config.get("domains") == "":
            return True
        domains = self.config.get("domains").split()
        return domain in domains

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
            # could refactor this - is a bit redundant
            if self.allowed_domain(path):
                resource_type = MissingDomainResource
            else:
                resource_type = ForbiddenDomainResource
            return resource_type(path, self.dnsserver.factory)

class MiniDNSSite(Site):

    def log(self, *a, **kw):
        pass

def webservice(config, dnsserver):
    root = RootResource(config, dnsserver)
    site = MiniDNSSite(root)
    return internet.TCPServer(config['www_port'], site)
