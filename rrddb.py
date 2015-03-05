#!/usr/bin/env python3
import time
import os
from GlobalRRD import GlobalRRD
from NodeRRD import NodeRRD


class RRD:
    def __init__(self, db_dir, image_dir,
                 display_time_global="7d", display_time_node="1d"):
        self.dbPath = db_dir
        self.globalDb = GlobalRRD(self.dbPath)
        self.imagePath = image_dir
        self.displayTimeGlobal = display_time_global
        self.displayTimeNode = display_time_node

        self.currentTimeInt = (int(time.time()) / 60) * 60
        self.currentTime = str(self.currentTimeInt)

        try:
            os.stat(self.imagePath)
        except FileNotFoundError:
            os.mkdir(self.imagePath)

    def update_database(self, db):
        nodes = db.get_nodes()
        clientcount = sum(map(lambda d: d.clientcount, nodes))

        curtime = time.time() - 60
        self.globalDb.update(len(list(filter(lambda x: x.lastseen >= curtime, nodes))), clientcount)
        for node in nodes:
            rrd = NodeRRD(
                os.path.join(self.dbPath, str(node.id).replace(':', '') + '.rrd'),
                node
            )
            rrd.update()

    def update_images(self):
        """ Creates an image for every rrd file in the database directory.
        """

        self.globalDb.graph(os.path.join(self.imagePath, "globalGraph.png"), self.displayTimeGlobal)

        nodedb_files = os.listdir(self.dbPath)

        for fileName in nodedb_files:
            if not os.path.isfile(os.path.join(self.dbPath, fileName)):
                continue

            nodename = os.path.basename(fileName).split('.')
            if nodename[1] == 'rrd' and not nodename[0] == "nodes":
                rrd = NodeRRD(os.path.join(self.dbPath, fileName))
                rrd.graph(self.imagePath, self.displayTimeNode)
