#!/usr/bin/env python3
import subprocess
import json


class Alfred:
    def __init__(self):
        pass

    def get_data(self):
        json_nodeinfo = subprocess.check_output(
            ['alfred-json', '-r', '158', '-f', 'json', '-z'])
        json_statistics = subprocess.check_output(
            ['alfred-json', '-r', '159', '-f', 'json', '-z'])

        nodeinfo = json.loads(json_nodeinfo.decode('utf-8'))
        statistics = json.loads(json_statistics.decode('utf-8'))

        # merge alfred data by mac address
        for k in nodeinfo:
            if k in statistics:
                nodeinfo[k].update(statistics[k])
            else:
                nodeinfo[k] = statistics[k]

        return nodeinfo

    def lookup(self):
        alfred_data = self.get_data()

        data = {}
        for mac, node in alfred_data.items():
            node_alias = {}

            # gps location
            if 'location' in node:
                try:
                    node_alias['gps'] = "%s %s" % (node['location']['latitude'], node['location']['longitude'])
                except KeyError:
                    pass

            # client count (since gluon 2014.4)
            try:
                node_alias['clientcount'] = node['clients']['total']
            except KeyError:
                pass

            # firmware version
            try:
                node_alias['firmware'] = node['software']['firmware']['release']
            except KeyError:
                pass

            # mac address
            try:
                node_alias['id'] = node['network']['mac']
            except KeyError:
                pass

            # hostname
            if 'hostname' in node:
                node_alias['name'] = node['hostname']
            elif 'name' in node:
                node_alias['name'] = node['name']

            if len(node_alias):
                data[mac] = node_alias
        return data


if __name__ == '__main__':
    ad = Alfred()
    al = ad.lookup()
    print(al)
