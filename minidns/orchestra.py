
import subprocess

from twisted.application import service

from .dns import DNSService
from .restapi import webservice

class OrchestrationService(service.MultiService):

    """ Handles starting and stopping. """

    def __init__(self, conf):
        service.MultiService.__init__(self)
        self.conf = conf
        self.dnsserver = DNSService(conf)
        self.dnsserver.setServiceParent(self)
        self.webserver = webservice(conf, self.dnsserver)
        self.webserver.setServiceParent(self)

    def startService(self):
        service.MultiService.startService(self)
        self.port_forward()

    def stopService(self):
        service.MultiService.stopService(self)
        self.port_unforward()

    def iptables_cmd(self, action, port):
        command = [
            "iptables",
            "-tnat",
            action, "OUTPUT",
            "-p", "udp",
            "-d127.0.0.0/8",
            "--dport", "53",
            "-j", "REDIRECT",
            "--to-port", str(port),
        ]
        rv = subprocess.call(command)

    def iptables_divert(self):
        self.iptables_cmd("-A", self.conf['udp_port'])

    def iptables_undivert(self):
        self.iptables_cmd("-D", self.conf['udp_port'])

    def port_forward(self):
        self.iptables_divert()

    def port_unforward(self):
        self.iptables_undivert()

