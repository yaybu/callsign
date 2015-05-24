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


""" ConfigParser is a load of rubbish. """

import os
from ConfigParser import ConfigParser


def get_forwarders(resolv="resolv.conf"):
    """ Find the forwarders in /etc/resolv.conf, default to 8.8.8.8 and
    8.8.4.4 """
    ns = []
    if os.path.exists(resolv):
        for l in open(resolv):
            if l.startswith("nameserver"):
                address = l.strip().split(" ", 2)[1]
                # forwarding to ourselves would be bad
                if not address.startswith("127"):
                    ns.append(address)
    if not ns:
        ns = ['8.8.8.8', '8.8.4.4']
    return ns

defaults = {
    "pidfile": "/var/run/callsign.pid",
    "logfile": "/var/log/callsign.log",
    "udp_port": "53",
    "www_port": "5080",
    "domains": "",
    "forwarders": " ".join(get_forwarders()),
    "savedir": "/var/lib/callsign",
    "forward": "true",
    "rewrite": "true",
    "user": "callsign",
}

int_fields = ["udp_port", "www_port"]
bool_fields = ["forward", "rewrite"]


def to_bool(x):
    if x.lower() in ("true", "yes", "on", "1"):
        return True
    elif x.lower() in ("false", "no", "off", "0"):
        return False
    else:
        raise ValueError("%r in config file is not boolean" % x)


def config(pathname):
    if pathname is not None:
        cp = ConfigParser()
        cp.read(pathname)

        def get(name, default):
            if cp.has_option("callsign", name):
                return cp.get("callsign", name)
            else:
                return default

    else:

        def get(name, default):
            return default

    d = {}
    for name, default in defaults.items():
        d[name] = get(name, default)
        if name in int_fields:
            d[name] = int(d[name])
        elif name in bool_fields:
            d[name] = to_bool(d[name])
    return d
