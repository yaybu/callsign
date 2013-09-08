from zope.interface import implements
from twisted.application import internet
from twisted.web.server import Site
from twisted.web.resource import Resource

class RootResource(Resource):

    def __init__(self, config, dnsserver):
        self.config = config
        self.dnsserver = dnsserver

def webservice(config, dnsserver):
    root = RootResource(config, dnsserver)
    site = Site(root)
    return internet.TCPServer(config.www_port, site)
