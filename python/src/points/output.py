from points.point import IoPoint


class Output(IoPoint):
    def __init__(self, io_manager, key, name, description, device_type, pin, topic, interval, value, invert, shift_register_key):
        super().__init__(
            key, name, description, value, invert, topic, interval)

        self.device_type = device_type
        self.pin = pin
        self.shift_register_key = shift_register_key
        self._io_manager = io_manager

        self.value = 0

    def tick(self, topic_host_name):
        # Has any defined interval expired
        if not super().interval_expired():
            # No, then do no processing this tick
            return

        # Use IO manager to set ouput (GPIO or SR)
        self._io_manager.output(self.key, self.value)

        # Return topic (if template defined)
        return self._build_state_topic(topic_host_name)

    def set_value(self, value):
        # Convert byte string values sent from MQTT to int bit values
        if value == b'1':
            value = 1
        elif value == b'0':
            value = 0

        self.value = value

    def mqtt_callback(self, value, topic_host_name):
        # Set output value
        self.set_value(value)

        return self._build_state_topic(topic_host_name)

    def _build_state_topic(self, topic_host_name):
        # Return topic (if template defined)
        return super().build_topic(topic_host_name, action="state")
