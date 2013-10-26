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

from twisted.scripts.twistd import run as twistd_run
from twisted.python.util import sibpath
import sys
import os
from subprocess import call, check_call
import optparse
import requests

from minidns.config import config
from minidns.client import MiniDNSClient

usage = """%prog [options] command

daemon control commands:
    start  start the minidns server and forward localhost:53 to it
    stop   stop the minidns server and remove iptables rules

zone commands:
    list      list all authoritative zones
    purge     delete all domains
    add name  add a new local authoritative zone "name"
    del name  delete the local authoritative zones "name"
    show name list records for the zone "name"

record commands:
    record [zone] a [host] [data]   create A record
    record [zone] del [host]        delete record

    e.g. record example.com a www 192.168.0.1"""

def run():
    parser = optparse.OptionParser(usage=usage)
    parser.add_option("-c", "--config", help="path to configuration file")
    parser.add_option("-n", "--no-divert", action="store_true", help="Do not use iptables to divert port DNS locally")
    opts, args = parser.parse_args()

    if len(args) == 0:
        parser.print_help()
        raise SystemExit(-1)

    if args[0] in ("start", "stop", "list", "purge"):
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
    elif args[0] == "purge":
        client.zone_purge()
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
    else:
        parser.print_help()
        return 255
