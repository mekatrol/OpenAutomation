from points.point import IoPoint


class Virtual(IoPoint):
    def __init__(self, io_manager, key, name, description, value, topic, interval, mqtt_publish_interval):
        super().__init__(
            key, name, description, value, False, topic, interval, mqtt_publish_interval)

    def tick(self, topic_host_name):
        # Has any defined interval expired
        if not super().interval_expired():
            # No, then do no processing this tick
            return

        if self.mqtt_publish_tick(topic_host_name):
            # Return built topic (if topic template defined)
            return super().build_topic(topic_host_name, action="state")

        return None

    def mqtt_callback(self, value, topic_host_name):

        # Update value
        self.value = float(value)

        # Send state out to listeners
        return super().build_topic(topic_host_name, action="state")
