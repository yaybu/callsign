from twisted.scripts.twistd import run as twistd_run
from twisted.python.util import sibpath
import sys
import os
from subprocess import call, check_call
import optparse
import requests

from minidns.config import config

usage = """%prog [options] command

daemon control commands:
    start  start the minidns server and forward localhost:53 to it
    stop   stop the minidns server and remove iptables rules

zone commands:
    add name  add a new local authoritative zone "name"
    del name  delete the local authoritative zones "name"
    list      list all authoritative zones
    show name list records for the zone "name"

record commands:
    record zone a host [data]   create A record
    record zone del host        delete record

    e.g. record example.com a www 192.168.0.1


"""

class MiniDNSClient:

    def __init__(self, opts, conf):
        self.opts = opts
        self.conf = conf

    def iptables_cmd(self, action, protocol, port):
        command = [
            "sudo", "iptables",
            "-tnat",
            action, "OUTPUT",
            "-p", protocol,
            "-d127.0.0.0/8",
            "--dport", "53",
            "-j", "REDIRECT",
            "--to-port", str(port),
        ]
        rv = call(command)

    def iptables_divert(self):
        self.iptables_cmd("-A", "tcp", self.conf['tcp_port'])
        self.iptables_cmd("-A", "udp", self.conf['udp_port'])

    def iptables_undivert(self):
        self.iptables_cmd("-D", "tcp", self.conf['tcp_port'])
        self.iptables_cmd("-D", "udp", self.conf['udp_port'])

    def start(self):
        if not self.opts.no_divert:
            self.iptables_divert()
        if self.opts.config is not None:
            os.environ["MINIDNS_CONFIG_FILE"] = opts.config
        sys.argv[1:] = [
            "-oy", sibpath(__file__, "minidns.tac"),
            "--pidfile", self.conf['pidfile'],
            "--logfile", self.conf['logfile'],
        ]
        twistd_run()

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
        except OSError:
            print "minidns is not running"

    @property
    def base_url(self):
        return "http://localhost:%s" % self.conf['www_port']

    def zone_list(self):
        response = requests.get(self.base_url).text
        if response:
            print response

    def zone_add(self, name):
        requests.put("%s/%s" % (self.base_url, name))

    def zone_del(self, name):
        requests.delete("%s/%s" % (self.base_url, name))

    def zone_show(self, name):
        response = requests.get("%s/%s" % (self.base_url, name)).text
        if response:
            print response

    def record_a(self, zone, host, data):
        requests.put("%s/%s/%s" % (self.base_url, zone, host), data=data)

    def record_del(self, zone, host):
        requests.delete("%s/%s/%s" % (self.base_url, zone, host))


def run():
    parser = optparse.OptionParser(usage=usage)
    parser.add_option("-c", "--config", help="path to configuration file")
    parser.add_option("-n", "--no-divert", action="store_true", help="Do not use iptables to divert port DNS locally")
    opts, args = parser.parse_args()

    if len(args) == 0:
        parser.print_help()
        raise SystemExit(-1)

    if args[0] in ("start", "stop", "list"):
        if len(args) != 1:
            parser.print_help()
            raise SystemExit(-1)
    elif args[0] == "record":
        pass
    elif len(args) != 2:
        parser.print_help()
        raise SystemExit(-1)

    conf = config(opts.config)
    client = MiniDNSClient(opts, conf)

    if args[0] == "start":
        client.start()
    elif args[0] == "stop":
        client.stop()
    elif args[0] == "list":
        client.zone_list()
    elif args[0] == "add":
        client.zone_add(args[1])
    elif args[0] == "del":
        client.zone_del(args[1])
    elif args[0] == "show":
        client.zone_show(args[1])
    elif args[0] == "record":
        if len(args) < 4:
            parser.print_help()
            return 255
        zone = args[1]
        command = args[2]
        host = args[3]
        if command == "a":
            if len(args) != 5:
                parser.print_help()
                return 255
            data = args[4]
            client.record_a(zone, host, data)
        elif command == "del":
            client.record_del(zone, host)
    else:
        parser.print_help()
        return 255
