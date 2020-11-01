from points.point import IoPoint


class Virtual(IoPoint):
    def __init__(self, io_manager, key, name, description, value, topic, interval):
        super(self.__class__, self).__init__(
            key, name, description, value, topic, interval)

    def tick(self, topic_host_name):
        # Has any defined interval expired
        if not super(self.__class__, self).interval_expired():
            # No, then do no processing this tick
            return

        # Return built topic (if topic template defined)
        return super(self.__class__, self).build_topic(topic_host_name, action="state")
