from zope.interface import implements
from twisted.application import internet
from twisted.web.server import Site
from twisted.web.resource import Resource, NoResource

class RecordResource(Resource):

    def __init__(self, name, domain, config, dnsserver):
        Resource.__init__(self)
        self.name = name
        self.domain = domain
        self.config = config
        self.dnsserver = dnsserver

    def render_POST(self, request):
        data = request.content
        request.setResponseCode(201)
        return ""

class DomainResource(Resource):

    def __init__(self, domain, config, dnsserver):
        Resource.__init__(self)
        self.domain = domain
        self.config = config
        self.dnsserver = dnsserver

    def render_PUT(self, request):
        print request.__dict__
        request.setResponseCode(201)
        return ""

    def render_GET(self, request):
        return "www 192.168.0.1"

    def getChild(self, path, request):
        return RecordResource(path, self.domain, self.config, self.dnsserver)

class RootResource(Resource):

    def __init__(self, config, dnsserver):
        Resource.__init__(self)
        self.config = config
        self.dnsserver = dnsserver

    def render_GET(self, request):
        return self.config.domain + "\n"

    def getChild(self, path, request):
        if path == "":
            return self
        if path == self.config.domain:
            return DomainResource(path, self.config, self.dnsserver)
        else:
            return NoResource()

def webservice(config, dnsserver):
    root = RootResource(config, dnsserver)
    site = Site(root)
    return internet.TCPServer(config.www_port, site)
