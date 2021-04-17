from points.point import IoPoint


class Input(IoPoint):
    def __init__(self, io_manager, key, name, description, device_type, pin, pud, topic, interval, mqtt_publish_interval, value, invert):
        super().__init__(
            key, name, description, value, invert, topic, interval, mqtt_publish_interval)

        self.device_type = device_type
        self.pin = pin
        self.pud = pud
        self._io_manager = io_manager
        self._mqtt_publish_tick_count = 0

    def tick(self, topic_host_name):
        # Has any defined interval expired
        if not super().interval_expired():
            # No, then do no processing this tick
            return

        # Get the current value (io manager takes care of inverted flag for us)
        self.value = self._io_manager.input(self.key)

        if self.mqtt_publish_tick(topic_host_name):
            # Return built topic (if topic template defined)
            return super().build_topic(topic_host_name)

        return None
