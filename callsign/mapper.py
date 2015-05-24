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


from twisted.names.dns import (
    QUERY_TYPES,
    Record_A, Record_CNAME, Record_MX, Record_TXT, Record_NS
)

record_types = {'A': Record_A, 'CNAME': Record_CNAME, 'TXT': Record_TXT, 'NS': Record_NS, 'MX': Record_MX}

# These record types can match hostnames if the specifed attr differs
unique_attr_map = {'A': 'address', 'CNAME': 'name', 'TXT': 'data', 'NS': 'name', 'MX': 'name'}


# Generic approach
def get_typestring(rinstance):
    return QUERY_TYPES[rinstance.TYPE]


def get_values(rinstance):
    return get_attrs(rinstance).values()


def get_attrs(rinstance):
    # create list of tuples of record attrs and values - using compareattributes
    attrs = zip(rinstance.compareAttributes,
                map(lambda a: _getattrvalue(rinstance, a),
                    rinstance.compareAttributes))
    # strip None values and return a dict
    return dict([(k, v) for k, v in attrs if v != 'None'])


# special case IP and text data - is there a canonical representation for TTL?
def _getattrvalue(rinstance, attr):
    if attr == 'address':
        return rinstance.dottedQuad()
    if attr == 'data':
        return getattr(rinstance, 'data')
    else:
        return str(getattr(rinstance, attr))
