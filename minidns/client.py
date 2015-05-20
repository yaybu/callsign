
import requests
import json


class MiniDNSClient:

    def __init__(self, opts, conf):
        self.opts = opts
        self.conf = conf

    @property
    def base_url(self):
        return "http://localhost:%s" % self.conf['www_port']

    def handle_error(self, response, errordict=()):
        if response.status_code in errordict:
            print errordict[response.status_code]
        else:
            print "Error:", response.reason
        raise SystemExit(255)

    def zone_list(self):
        response = requests.get(self.base_url)
        if response.status_code == 200:
            if response.text:
                print response.text
        else:
            self.handle_error(response)

    def zone_purge(self):
        response = requests.get(self.base_url)
        if response.status_code == 200:
            for zone in response.text.split():
                self.zone_del(zone)
        else:
            self.handle_error(response)

    def zone_add(self, name):
        response = requests.put("%s/%s" % (self.base_url, name))
        if response.status_code != 201:
            self.handle_error(response, {
                409: "Domain data already exists. Delete first.",
                400: "Invalid request.",
                403: "Forbidden: domain is not allowed."
            })

    def zone_del(self, name):
        response = requests.delete("%s/%s" % (self.base_url, name))
        if response.status_code != 204:
            self.handle_error(response, {
                404: "Error: Zone %r is not managed by minidns" % name,
            })

    def zone_show(self, name):
        response = requests.get("%s/%s" % (self.base_url, name))
        if response.status_code != 200:
            self.handle_error(response, {
                404: "Error: Zone %r is not managed by minidns" % name
            })
        else:
            if response.text:
                for line in response.text.split("\n"):
                    type_, host, values = line.split(' ', 2)
                    print host, type_, values
            else:
                print "Zone %s is managed, but there are no records for it" % name

    # Probably should refactor to be generic like in dns.py
    def record_a(self, zone, host, ip, ttl):
        url = "%s/%s" % (self.base_url, zone)
        payload = {host: {'type': 'A', 'address': ip}}
        if ttl:
            payload[host]['ttl'] = ttl
        headers = {'content-type': 'application/json'}
        response = requests.put(url, data=json.dumps(payload), headers=headers)
        if response.status_code != 201:
            self.handle_error(response, {
                404: "Error: Zone %r is not managed by minidns" % zone,
                400: response.reason
            })

    def record_txt(self, zone, host, data, ttl):
        url = "%s/%s" % (self.base_url, zone)
        payload = {host: {'type': 'TXT', 'data': [data]}}
        if ttl:
            payload[host]['ttl'] = ttl
        headers = {'content-type': 'application/json'}
        response = requests.put(url, data=json.dumps(payload), headers=headers)
        if response.status_code != 201:
            self.handle_error(response, {
                404: "Error: Zone %r is not managed by minidns" % zone,
                400: response.reason
            })

    def record_simple(self, zone, type_, host, name, ttl):
        url = "%s/%s" % (self.base_url, zone)
        payload = {host: {'type': type_, 'name': name}}
        if ttl:
            payload[host]['ttl'] = ttl
        headers = {'content-type': 'application/json'}
        response = requests.put(url, data=json.dumps(payload), headers=headers)
        if response.status_code != 201:
            self.handle_error(response, {
                404: "Error: Zone %r is not managed by minidns" % zone,
                400: response.reason
            })

    def record_del(self, zone, host):
        response = requests.delete("%s/%s/%s" % (self.base_url, zone, host))
        if response.status_code != 204:
            self.handle_error(response, {
                404: "Error: Record not found",
            })
