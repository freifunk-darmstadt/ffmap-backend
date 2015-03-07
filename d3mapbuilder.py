import json
import datetime


class D3MapBuilder:
    def __init__(self, db):
        self._db = db

    def build(self):
        output = dict()

        now = datetime.datetime.utcnow().replace(microsecond=0)

        nodes = self._db.get_nodes()
        output['nodes'] = [{'name': node.name, 'id': node.id,
                            'geo': [float(x) for x in node.gps.split(" ")] if node.gps else None,
                            'firmware': node.firmware,
                            'flags': node.flags,
                            'clientcount': node.clientcount} for node in nodes]

        links = self._db.get_links()
        output['links'] = [{'source': link.source.id, 'target': link.target.id,
                            'quality': link.quality,
                            'type': link.type,
                            'id': link.id} for link in links]

        output['meta'] = {'timestamp': now.isoformat()}

        return json.dumps(output)
