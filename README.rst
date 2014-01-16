=======
minidns
=======

:Date: 2013-09-11
:Author: Doug Winter <doug.winter@isotoma.com>
:Website: http://github.com/yaybu/minidns

Description
===========

MiniDNS is a DNS server for developers. It is intended to serve DNS only for a
single machine - your desktop. It will support automated deployment systems
that coordinate with DNS services, for example Yaybu.

Desktops vary in their client DNS configuration quite widely, and MiniDNS
supports a number of different modes to enable it to service your DNS effectively.

The DNS service provides recursive queries, so you can continue to use DNS as usual.

You can then set new authoritative domains and A records that are available
locally.

For example::

    $ minidns start
    $ host www.example.com
    www.example.com has address 93.184.216.119
    www.example.com has IPv6 address 2606:2800:220:6d:26bf:1447:1097:aa7
    $ minidns add example.com
    $ minidns record example.com a www 192.168.0.10
    $ minidns show example.com
    www 192.168.0.10
    $ host www.example.com
    www.example.com has address 192.168.0.10
    $ minidns stop
    $ host www.example.com
    www.example.com has address 93.184.216.119
    www.example.com has IPv6 address 2606:2800:220:6d:26bf:1447:1097:aa7

Usage::

    Usage: minidns [options] command

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

    Options:
      -h, --help            show this help message and exit
      -c CONFIG, --config=CONFIG
                            path to configuration file

Modes of operation
==================

For the standard libc resolver DNS services must be provided on port 53 - there
is no option for the resolver to consult other ports.

MiniDNS must therefore either run on udp port 53 (which means it must be
started as root), or run on a high port and have some form of port-forwarding
configured (which also requires root).

If you already have a nameservice running locally (which is not uncommon) then
you may wish to use the port-forwarding features.  This makes minidns as uninvasive as possible.

Note that minidns drops privileges once ports are bound, it does not continue to run as root.

The user that minidns runs as (by default, 'minidns') must already exist on the system. If not installed
by the package manager, run something like:

    sudo useradd -r -s /bin/false minidns

The standard configuration for the libc resolver is in /etc/resolv.conf. This
file will need to have only a single nameserver, 127.0.0.1, configured for
MiniDNS to work. MiniDNS provides options to overwrite the configuration in
resolv.conf as part of starting up. It will then replace the previous
configuration when it is stopped.

Finally MiniDNS requires "forwarders" - other servers that will answer
recursive queries for domains for which MiniDNS is not authoritative.

MiniDNS attempts to provide intelligent behaviour by default so that none of these things need to be configured manually, as follows:

    1. on starting it will read /etc/resolv.conf. If this does not contain a 127.0.0.1 nameserver then it will read the nameservers and use them as forwarders, otherwise it will use the forwarders from the configuration file or 8.8.8.8 / 8.8.4.4 as fallbacks.
    2. it will then attempt to bind to port 53 locally.
    3. if it cannot bind to port 53 because it is in use then it will bind to the port configured in the configuration file (or 5053 by default) and trigger port-forwarding behaviour (as below)
    4. if the resolv.conf file did not contain 127.0.0.1 then it is copied to /etc/resolv.conf.minidns and the original rewritten to use 127.0.0.1
    5. resolv.conf is monitored for changes (your dhcp client might do this) and is automatically rewritten as required.

port-forwarding:

    1. if a "port-forward" configuration option is provided, then it is executed
    2. otherwise, if the "iptables" program is available, then appropriate iptables incantations are used.
    3. if neither of these options is available then the program will terminate with an error, and you will need to provide configuration

When the server is stopped it will:

    1. put the resolv.conf file back as it was before, if it was rewritten
    2. stop port-forwarding, either by using the port-unforward option or by using iptables, as appropriate


resolv.conf file management
---------------------------

A small daemon is run as root by minidns that manages the resolv.conf file. It performs the following operations:

On starting it:

  1. copies /etc/resolv.conf to /etc/resolv.conf.minidns
  2. writes a new /etc/resolv.conf that uses 127.0.0.1 as the nameserver
  
It then regularly checks the modification date on /etc/resolv.conf. If it is newer than the last change it made itself then it rewrites it again.

On exit it copies the contents of /etc/resolv.conf.minidns into /etc/resolv.conf

Configuring behaviour
---------------------

You can force particular behaviours by setting the "forward" and "rewrite" configuration options:

forward
-------

If this is "true" then the server will not attempt to bind to port 53. If this is "false" then the server will bail if it cannot bind to port 53.

rewrite
-------

If rewrite is false then the server will not attempt to rewrite resolv.conf, but it will still start even if the resolv.conf file does not refer to 127.0.0.1.

Configuration file
==================

A configuration file is not required. Note that Google's DNS servers are used as fallback forwarders by default, as described above.

If you wish, you can provide a file with the following format (defaults are shown)::

    [minidns]
    forwarders = 8.8.8.8 8.8.4.4
    udp_port = 5053
    www_port = 5080
    pidfile = /var/run/minidns.pid
    logfile = /var/log/minidns.log
    domains =
    savedir = /var/lib/.minidns
    port-forward = iptables -tnat -A OUTPUT -p udp -d127.0.0.1/8 --dport 53 -j REDIRECT --to-port {port}
    port-unforward = iptables -tnat -D OUTPUT -p udp -d127.0.0.1/8 --dport 53 -j REDIRECT --to-port {port}
    forward = true
    rewrite = true
    user = minidns

If any domains are listed then only those domains will be allowed::

    domains foo.com bar.com baz.com



API
===

MiniDNS is designed primarily to be used by automated deployment systems, and
provides a simple REST API for these systems.

In general you should expect the following response codes on a successful request:

 * GET requests return 200 on success
 * PUT requests return 201 on success
 * DELETE requests return 204 on success

The resources available on the web port are:

Root resource: /
----------------

GET
~~~

Return a list of managed zones, one per line, separated by \n.  For example::

    GET /

    200 OK
    example.com
    foo.com

Possible status code responses are:

 * *200* Success

Domain resource: /domain
------------------------

GET
~~~

Return the list of records within this domain, one per line, separated by \n.  For example::

    GET /example.com

    200 OK
    A www 192.168.0.1

Possible status code responses are:

 * *200* Success
 * *404* Domain not found. The domain has not been created as an authoritative zone in minidns.

PUT
~~~

Create this domain.  For example::

    PUT /example.com

    201 Created

Possible status code responses are:

 * *201* Created (success)
 * *200* Domain already exists, unchanged
 * *403* Domain is forbidden (it is not in the list of allowed domains in the configuration file)

DELETE
~~~~~~

Delete this domain.  For example::

    DELETE /example.com

    204 No Content

Possible status code responses are:

 * *204* Success
 * *404* Domain not found. The domain has not been created as an authoritative zone in minidns.

Record resource: /domain/host
-----------------------------

GET
~~~

Return the value for the record.  For example::

    GET /example.com/www

    200 OK
    A 192.168.0.1

Possible status code responses are:

 * *200* Success
 * *404* Record not found

PUT
~~~

Create the record. the payload should be the type and the data, separated by a space.  For example::

    PUT /example.com/www
    A 192.168.0.1

    201 Created

Possible status code responses are:

 * *201* Created (success)
 * *404* Zone not found
 * *400* Malformed request. The reason message will provide more details.

DELETE
~~~~~~

Delete the record. For example::

    DELETE /example.com/www

    204 No Content

Possible status code responses are:

 * *204* Success
 * *404* Domain or record not found

LICENSE
=======

Copyright 2013 Isotoma Limited

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

