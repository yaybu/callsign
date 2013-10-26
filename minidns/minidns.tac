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


from twisted.application import service

from minidns.dns import DNSService
from minidns.restapi import webservice
from minidns.config import config

import os

config_file = os.environ.get("MINIDNS_CONFIG_FILE", None)
conf = config(config_file)

application = service.Application("minidns")

dnsserver = DNSService(conf)
dnsserver.setServiceParent(application)

webserver = webservice(conf, dnsserver)
webserver.setServiceParent(application)

