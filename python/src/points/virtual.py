from points.point import IoPoint

class Virtual(IoPoint):
    def __init__(self, io_manager, key, name, description, topic, interval):
        super(self.__class__, self).__init__(key, name, description, topic, interval)