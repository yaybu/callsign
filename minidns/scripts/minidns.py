from twisted.scripts.twistd import run as twistd_run
from twisted.python.util import sibpath
import sys
import os
from subprocess import call, check_call
import optparse
from ConfigParser import ConfigParser

usage = "%prog [options] {start|stop}"

def iptables_cmd(action, protocol, port):
    command = [
        "sudo", "iptables",
        "-tnat",
        action, "OUTPUT",
        "-p", protocol,
        "-d127.0.0.0/8",
        "--dport", "53",
        "-j", "REDIRECT",
        "--to-port", port,
    ]
    rv = check_call(command)

def iptables_divert(tcp_port, udp_port):
    iptables_cmd("-A", "tcp", tcp_port)
    iptables_cmd("-A", "udp", udp_port)

def iptables_undivert(tcp_port, udp_port):
    iptables_cmd("-D", "tcp", tcp_port)
    iptables_cmd("-D", "udp", udp_port)

def run():
    parser = optparse.OptionParser(usage=usage)
    parser.add_option("-c", "--config", default="/etc/minidns.conf", help="path to configuration file")
    parser.add_option("-n", "--no-divert", action="store_true", help="Do not use iptables to divert port DNS locally")
    opts, args = parser.parse_args()

    if len(args) != 1:
        parser.print_help()
        raise SystemExit(-1)

    if not os.path.exists(opts.config):
        print "Cannot read config file", opts.config
        return 254

    cp = ConfigParser()
    cp.read(opts.config)

    if cp.has_option("minidns", "pidfile"):
        pidfile = cp.get("minidns", "pidfile")
    else:
        pidfile = "/var/run/minidns/minidns.pid"
    if cp.has_option("minidns", "logfile"):
        logfile = cp.get("minidns", "logfile")
    else:
        logfile = "/var/log/minidns.log"

    if args[0] == "start":
        if not opts.no_divert:
            iptables_divert(cp.get("minidns", "tcp_port"),
                            cp.get("minidns", "udp_port"))
        os.environ["MINIDNS_CONFIG_FILE"] = opts.config
        sys.argv[1:] = [
            "-oy", sibpath(__file__, "minidns.tac"),
            "--pidfile", pidfile,
            "--logfile", logfile,
        ]
        twistd_run()
    elif args[0] == "stop":
        if not opts.no_divert:
            iptables_undivert(cp.get("minidns", "tcp_port"),
                              cp.get("minidns", "udp_port"))
        try:
            pid = int(open(pidfile).read())
        except IOError:
            print "minidns is not running"
            return 255
        os.kill(pid, 15)
    else:
        parser.print_help()
        return 255
