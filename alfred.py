import subprocess
import json


class Alfred(object):
    """
    Bindings for the alfred-json utility
    """

    def __init__(self, socket='/run/alfred.sock'):
        self.socket = socket

    def query(self):
        """
        Query alfred-json for data types 158 (nodeinfo) and 159 (statistics)
        and merge received data by mac addresses
        """
        json_nodeinfo = subprocess.check_output(
            ['alfred-json',
             '-s', self.socket,
             '-r', '158',
             '-f', 'json',
             '-z'])
        json_statistics = subprocess.check_output(
            ['alfred-json',
             '-s', self.socket,
             '-r', '159',
             '-f', 'json',
             '-z'])

        nodeinfo = json.loads(json_nodeinfo.decode('utf-8'))
        statistics = json.loads(json_statistics.decode('utf-8'))

        # merge by mac address
        for k in nodeinfo:
            if k in statistics:
                nodeinfo[k].update(statistics[k])
            else:
                nodeinfo[k] = statistics[k]

        return nodeinfo

    def lookup(self):
        """
        Extract alfred data for use in NodeDB
        """
        alfred_data = self.query()

        tmp = {}
        for mac, data in alfred_data.items():
            node = {}

            # gps location
            if 'location' in node:
                try:
                    node['gps'] = (data['location']['latitude'],
                                   data['location']['longitude'])
                except KeyError:
                    pass

            # client count (via alfred since gluon 2014.4)
            try:
                node['clientcount'] = data['clients']['total']
            except KeyError:
                pass

            # firmware version
            try:
                node['firmware'] = data['software']['firmware']['release']
            except KeyError:
                pass

            # mac address
            try:
                node['id'] = data['network']['mac']
            except KeyError:
                pass

            # hostname
            try:
                node['name'] = data['hostname']
            except KeyError:
                pass

            if len(node):
                tmp[mac] = node

        return tmp
