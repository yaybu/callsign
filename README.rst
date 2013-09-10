=======
minidns
=======

Description
===========

Small DNS service to support local development. The server listens by default
on port 5053. iptables is used to forward requests to localhost:53 to localhost:5053 instead.

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

    Usage: minidns [options] {start|stop|add name|del name|list|show name|a fqdn ip}
    daemon control:
        start  start the minidns server and forward localhost:53 to it
        stop   stop the minidns server and remove iptables rules

    zone commands:
        add name  add a new local authoritative zone "name"
        del name  delete the local authoritative zones "name"
        list      list all authoritative zones
        show name list records for the zone "name"

    record maintenance:
        record zone a host [data]   create A record
        record zone del host        delete record

        e.g. record example.com a www 192.168.0.1

    Options:
      -h, --help            show this help message and exit
      -c CONFIG, --config=CONFIG
                            path to configuration file
      -n, --no-divert       Do not use iptables to divert port DNS locally
