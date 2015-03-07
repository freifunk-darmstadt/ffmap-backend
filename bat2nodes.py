#!/usr/bin/env python3
import json
import argparse
import os
import time
from batman import Batman
from alfred import Alfred
from rrddb import RRD
from nodedb import NodeDB
from d3mapbuilder import D3MapBuilder

# Force encoding to UTF-8
import locale  # Ensure that subsequent open()s are UTF-8 encoded.
locale.getpreferredencoding = lambda _=None: 'UTF-8'


def main(options):
    nodedb = NodeDB(int(time.time()))

    for mesh_interface in options['mesh']:
        batman = Batman(mesh_interface)
        nodedb.parse_vis_data(batman.batadv_vis())
        for gw in batman.gateways():
            nodedb.mark_gateway(gw)

    if options['aliases']:
        for aliases in options['aliases']:
            nodedb.import_alfred_data(json.load(open(aliases)))

    if options['alfred']:
        alfred = Alfred()
        nodedb.import_alfred_data(alfred.lookup())

    # load historic data, prune inactive nodes, and save it
    nodedb.load_state("state.json")
    nodedb.prune_offline(time.time() - 30 * 86400)
    nodedb.dump_state("state.json")

    # d3.js graph builder
    map_builder = D3MapBuilder(nodedb)

    # write nodes json, and when finished, move to proper location
    nodes_json = open(options['dest'] + '/nodes.json.new', 'w')
    nodes_json.write(map_builder.build())
    nodes_json.close()

    os.rename(options['dest'] + '/nodes.json.new',
              options['dest'] + '/nodes.json')

    # render graphs (this becomes really cpu consuming the more nodes you have)
    scriptdir = os.path.dirname(os.path.realpath(__file__))
    rrd = RRD(db_dir=scriptdir + "/nodedb/",
              image_dir=options['dest'] + "/nodes")
    rrd.update_database(nodedb)
    rrd.update_images()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument('-a', '--aliases', help='read aliases from FILE',
                        action='append', metavar='FILE')
    parser.add_argument('-m', '--mesh', action='append', default=["bat0"],
                        help='batman mesh interface')
    parser.add_argument('-A', '--alfred', action='store_true',
                        help='retrieve aliases from alfred')
    parser.add_argument('-d', '--dest', action='store',
                        help='destination directory for generated files',
                        required=True)

    args = parser.parse_args()
    main(vars(args))
