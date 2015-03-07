import json
from functools import reduce
from collections import defaultdict
from node import Node
from link import Link, LinkConnector


class NodeDB:
    def __init__(self, time=0):
        self.time = time
        self._nodes = []
        self._links = []

    # fetch list of links
    def get_links(self):
        self.update_vpn_links()
        return self.reduce_links()

    # fetch list of nodes
    def get_nodes(self):
        return self._nodes

    # remove all offlines nodes with lastseen < timestamp
    def prune_offline(self, timestamp):
        self._nodes = list(filter(lambda x: x.lastseen >= timestamp,
                                  self._nodes))

    # write persistent state to file
    def dump_state(self, filename):
        obj = []

        for node in self._nodes:
            obj.append({'id': node.id,
                        'name': node.name,
                        'clientcount': node.clientcount,
                        'lastseen': node.lastseen,
                        'firstseen': node.firstseen,
                        'geo': node.gps,
                        'hardware': node.hardware,
                        'firmware': node.firmware})

        with open(filename, "w") as f:
            json.dump(obj, f)

    # load persistent state from file
    def load_state(self, filename):
        try:
            with open(filename, "r") as f:
                obj = json.load(f)
                for n in obj:
                    try:
                        node = self.maybe_node_by_id(n['id'])
                    except KeyError:
                        node = Node()
                        node.id = n['id']
                        node.name = n['name']
                        node.lastseen = n['lastseen']
                        node.gps = n['geo']
                        self._nodes.append(node)

                    try:
                        node.firstseen = n['firstseen']
                    except KeyError:
                        pass

        except IOError:
            pass

    def maybe_node_by_mac(self, macs):
        for node in self._nodes:
            for mac in macs:
                if mac.lower() in node.macs:
                    return node

        raise KeyError

    def maybe_node_by_id(self, mac):
        for node in self._nodes:
            if mac.lower() == node.id:
                return node

        raise KeyError

    def parse_vis_data(self, vis_data):
        for x in vis_data:
            if 'of' in x:
                try:
                    node = self.maybe_node_by_mac((x['of'], x['secondary']))
                except KeyError:
                    node = Node()
                    node.lastseen = self.time
                    node.firstseen = self.time
                    node.flags['online'] = True
                    self._nodes.append(node)

                node.add_mac(x['of'])
                node.add_mac(x['secondary'])

        for x in vis_data:
            if 'router' in x:
                # TTs will be processed later
                if x['label'] == "TT":
                    continue

                try:
                    node = self.maybe_node_by_mac((x['router'], ))
                except KeyError:
                    node = Node()
                    node.lastseen = self.time
                    node.firstseen = self.time
                    node.flags['online'] = True
                    node.add_mac(x['router'])
                    self._nodes.append(node)

                try:
                    if 'neighbor' in x:
                        try:
                            node = self.maybe_node_by_mac((x['neighbor'], ))
                        except KeyError:
                            continue

                    if 'gateway' in x:
                        x['neighbor'] = x['gateway']

                    node = self.maybe_node_by_mac((x['neighbor'], ))
                except KeyError:
                    node = Node()
                    node.lastseen = self.time
                    node.firstseen = self.time
                    node.flags['online'] = True
                    node.add_mac(x['neighbor'])
                    self._nodes.append(node)

        for x in vis_data:
            if 'router' in x:
                # TTs will be processed later
                if x['label'] == "TT":
                    continue

                try:
                    if 'gateway' in x:
                        x['neighbor'] = x['gateway']

                    router = self.maybe_node_by_mac((x['router'], ))
                    neighbor = self.maybe_node_by_mac((x['neighbor'], ))
                except KeyError:
                    continue

                # filter TT links merged in previous step
                if router == neighbor:
                    continue

                link = Link()
                link.connect(source=LinkConnector(self._nodes.index(router), x['router']),
                             target=LinkConnector(self._nodes.index(neighbor), x['neighbor']))
                link.set_quality(x['label'])

                self._links.append(link)

        for x in vis_data:
            if 'primary' in x:
                try:
                    node = self.maybe_node_by_mac((x['primary'], ))
                except KeyError:
                    continue

                node.id = x['primary']

        for x in vis_data:
            if 'router' in x and x['label'] == 'TT':
                try:
                    node = self.maybe_node_by_mac((x['router'], ))
                    node.add_mac(x['gateway'])
                except KeyError:
                    pass

    def reduce_links(self):
        tmp_links = defaultdict(list)

        for link in self._links:
            tmp_links[link.id].append(link)

        links = []

        def reduce_link(a, b):
            a.id = b.id
            a.connect(source=b.source, target=b.target)
            a.set_type(b.type)
            a.set_quality(", ".join([x for x in (a.quality, b.quality) if x]))

            return a

        for k, v in tmp_links.items():
            new_link = reduce(reduce_link, v, Link())
            links.append(new_link)

        return links

    def import_alfred_data(self, data):
        for mac, entry in data.items():
            try:
                # try to find the node
                node = self.maybe_node_by_mac([mac])
            except KeyError:
                # else create an offline node
                node = Node()
                node.add_mac(mac)
                self._nodes.append(node)

            # look through data given by alfred and handle import
            for key, value in entry.items():
                if key == 'name':  # user-given node name
                    node.name = value
                elif key == 'id':  # hardware mac address
                    node.id = value
                elif key == 'clientcount':
                    node.clientcount = value
                elif key == 'vpn':
                    node.interfaces[mac].vpn = True
                elif key == 'gps':
                    node.gps = "%s %s" % value
                elif key == 'firmware':
                    node.firmware = value
                elif key == 'hardware':
                    node.hardware = value

                else:
                    print("import_alfred_data: unhandled key '%s' with value '%s' given" % (key, value))

    def mark_gateway(self, gateway):
        try:
            node = self.maybe_node_by_mac((gateway, ))
            node.flags['gateway'] = True
        except KeyError:
            print("WARNING: did not find gateway ", gateway, " in node list")

    def update_vpn_links(self):
        changes = 1
        while changes > 0:
            changes = 0
            for link in self._links:
                source_interface = self._nodes[link.source.id].interfaces[link.source.interface]
                target_interface = self._nodes[link.target.id].interfaces[link.target.interface]
                if source_interface.vpn or target_interface.vpn:
                    source_interface.vpn = True
                    target_interface.vpn = True
                    if link.type != "vpn":
                        changes += 1

                    link.type = "vpn"
