#   Copyright 2014 Isotoma Limited
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

# should probably incorporate this all straight into dns.py

import json
from twisted.names.dns import QUERY_TYPES, IRecord, Record_A, Record_SOA, Record_CNAME

record_types = {}

def gettypestring(record):
    return QUERY_TYPES[record.TYPE]

def getitems(record):
    if 'type' in record and record['type'] in record_types:
        valnames = record_types[record['type']].args
        items = {}
        for name in valnames:
            if name in record:
                items[name] = record[name]
        return items
    # more error handling?
    return None
    
def getstringrep(record):
    if hasattr(record, 'TYPE') and QUERY_TYPES[record.TYPE] in record_types:
        rtype = QUERY_TYPES[record.TYPE]
        return record_types[QUERY_TYPES[record.TYPE]].str_rep(record)
    # more error handling?    
    return None

def createrecord(record):
    items = getitems(record)
    if items:
        return record_types[record['type']].record_class(**items)
    return None

class MDRecord_A:
    record_class = Record_A
    args = ['address','ttl']
    
    @staticmethod
    def str_rep(ra):
        if isinstance(ra, Record_A):
            return {'address': ra.dottedQuad(), 'ttl': ra.ttl}
        return {}
    
record_types = {'A': MDRecord_A,}# 'SOA': MDRecord_SOA, 'CNAME': MDRecord_CNAME,}

