class Link():
    def __init__(self):
        self.id = None
        self.source = None
        self.target = None
        self.quality = None
        self.type = None

    def connect(self, source, target):
        self.source = source
        self.target = target

    def set_id(self, id):
        self.id = id

    def set_quality(self, quality):
        self.quality = quality

    def set_type(self, type):
        self.type = type


class LinkConnector():
    def __init__(self, id, interface):
        self.id = id
        self.interface = interface

    def __repr__(self):
        return "LinkConnector(%d, %s)" % (self.id, self.interface)
