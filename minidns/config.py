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
    "tcp_port": "5053",
    "udp_port": "5053",
    "www_port": "5080",
    "domain": "local.dev",
    "forwarders": "8.8.8.8 8.8.4.4",
    "statefile": "minidns.db",
}

int_fields = ["tcp_port", "udp_port", "www_port"]

def config(pathname):
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

