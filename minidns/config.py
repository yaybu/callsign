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

from ConfigParser import ConfigParser

defaults = {
    "pidfile": "minidns.pid",
    "logfile": "minidns.log",
    "udp_port": "5053",
    "www_port": "5080",
    "domains": "",
    "forwarders": "8.8.8.8 8.8.4.4",
    "statefile": "minidns.db",
}

int_fields = ["udp_port", "www_port"]

def get_resolv_nameservers():
    try:
        r = open("/etc/resolv.conf")
    except IOError:
        raise IOError("Unable to open /etc/resolv.conf, cannot find nameservers. Please list nameservers in the configuration file")
    for l in r:
        parts = l.split()
        if parts[0] == "nameserver":
            if not parts[1].startswith("127"):
                yield parts[1]

def set_forwarders():
    """ Try to identify which forwarders are used locally. """
    nameservers = list(get_resolv_nameservers())
    if nameservers:
        defaults['forwarders'] = " ".join(nameservers)

def config(pathname):
    set_forwarders()
    if pathname is not None:
        cp = ConfigParser()
        cp.read(pathname)
        def get(name, default):
            if cp.has_option("minidns", name):
                return cp.get("minidns", name)
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
    return d

