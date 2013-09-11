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
      -n, --no-divert       Do not use iptables to divert port DNS locally

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
 * *405* Domain already exists

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

