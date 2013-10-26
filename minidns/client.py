
from twisted.python import util
import os
import sys
from twisted.scripts import twistd
import subprocess
import requests

class MiniDNSClient:

    def __init__(self, opts, conf):
        self.opts = opts
        self.conf = conf

    def iptables_cmd(self, action, port):
        command = [
            "sudo", "iptables",
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

    def start(self):
        if not self.opts.no_divert:
            self.iptables_divert()
        if self.opts.config is not None:
            os.environ["MINIDNS_CONFIG_FILE"] = self.opts.config
        sys.argv[1:] = [
            "-oy", util.sibpath(__file__, "minidns.tac"),
            "--pidfile", self.conf['pidfile'],
            "--logfile", self.conf['logfile'],
        ]
        twistd.run()

    def stop(self):
        if not self.opts.no_divert:
            self.iptables_undivert()
        try:
            pid = int(open(self.conf['pidfile']).read())
        except IOError:
            print "minidns is not running"
            return 255
        try:
            os.kill(pid, 15)
            os.unlink(self.conf['pidfile'])
        except OSError:
            print "minidns is not running"

    @property
    def base_url(self):
        return "http://localhost:%s" % self.conf['www_port']

    def handle_error(self, response, errordict=()):
        if response.status_code in errordict:
            print errordict[response.status_code]
        else:
            print "Error:", response.reason
        raise SystemExit(255)

    def zone_list(self):
        response = requests.get(self.base_url)
        if response.status_code == 200:
            if response.text:
                print response.text
        else:
            self.handle_error(response)

    def zone_purge(self):
        response = requests.get(self.base_url)
        if response.status_code == 200:
            for zone in response.text.split():
                self.zone_del(zone)
        else:
            self.handle_error(response)

    def zone_add(self, name):
        response = requests.put("%s/%s" % (self.base_url, name))
        if response.status_code != 201:
            self.handle_error(response, {
                200: "Domain already exists. Not changed.",
                403: "Forbidden: domain is not allowed."
            })

    def zone_del(self, name):
        response = requests.delete("%s/%s" % (self.base_url, name))
        if response.status_code != 204:
            self.handle_error(response, {
                404: "Error: Zone %r is not managed by minidns" % name,
                })

    def zone_show(self, name):
        response = requests.get("%s/%s" % (self.base_url, name))
        if response.status_code != 200:
            self.handle_error(response, {
                404: "Error: Zone %r is not managed by minidns" % name
                })
        else:
            if response.text:
                for line in response.text.split("\n"):
                    type_, host, ip = line.split()
                    print host, type_, ip
            else:
                print "Zone %s is managed, but there are no records for it" % name

    def record_a(self, zone, host, data):
        response = requests.put("%s/%s/%s" % (self.base_url, zone, host), data="A %s" % data)
        if response.status_code != 201:
            self.handle_error(response, {
                404: "Error: Zone %r is not managed by minidns" % zone,
                400: response.reason
                })

    def record_del(self, zone, host):
        response = requests.delete("%s/%s/%s" % (self.base_url, zone, host))
        if response.status_code != 204:
            self.handle_error(response, {
                404: "Error: Record not found",
                })

