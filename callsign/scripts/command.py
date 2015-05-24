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

import optparse

from callsign.config import config
from callsign.client import CallsignClient

usage = """%prog [options] command

zone commands:
    list      list all authoritative zones
    purge     delete all domains
    add name  add a new local authoritative zone "name"
    del name  delete the local authoritative zones "name"
    show name list records for the zone "name"

record commands:
    record [zone] a [host] [data]      create A record
    record [zone] cname [host] [data]  create CNAME record
    record [zone] txt [host] [data]    create TXT record
    record [zone] ns [host] [data]     create NS record
    record [zone] del [host]           delete record

    e.g.

    record example.com a www 192.168.0.1
    record example.com cname mail www
    record example.com cname mail www.example.com.
    record example.com mx 10 mail
    record example.com mx 10 mail.other.com.
    record example.com ns ns2.example.com.
    record example.com txt joe "This is Joe"
"""


def run():
    parser = optparse.OptionParser(usage=usage)
    parser.add_option("-c", "--config", help="path to configuration file")
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
    client = CallsignClient(opts, conf)

    if args[0] == "list":
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
        ttl = ""
        # probably should refactor out commonalities
        if command == "a":
            if len(args) < 5 or len(args) > 6:
                parser.print_help()
                return 255
            ip = args[4]
            if len(args) == 6:
                ttl = args[5]
            client.record_a(zone, host, ip, ttl)
        # simple records
        elif command in ("cname", "ns"):
            if len(args) < 5 or len(args) > 6:
                parser.print_help()
                return 255
            name = args[4]
            if len(args) == 6:
                ttl = args[5]
            type_ = command.upper()
            client.record_simple(zone, type_, host, name, ttl)
        elif command == "txt":
            if len(args) < 5 or len(args) > 6:
                parser.print_help()
                return 255
            data = args[4]
            if len(args) == 6:
                ttl = args[5]
            client.record_txt(zone, host, data, ttl)
        elif command == "del":
            client.record_del(zone, host)
        else:
            parser.print_help()
            return 255
    else:
        parser.print_help()
        return 255
