class Output:
    def __init__(self, io_manager, key, name, device_type, pin, topic, interval, shift_register_key):
        self.key = key
        self.name = name
        self.device_type = device_type
        self.pin = pin
        self.topic = topic
        self.interval = interval
        self.shift_register_key = shift_register_key
        self._io_manager = io_manager

        self.value = 0
        self._count_down = self.interval

    def tick(self, topic_host_name):
        # Use interval if defined
        if self.interval != None:

            # Decrement count down
            self._count_down -= 1

            # Count down not reached zero (interval incomplete)?
            if self._count_down > 0:
                return

            # Reset countdown from interval
            self._count_down = self.interval

        # Use IO manager to set ouput (GPIO or SR)
        self._io_manager.output(self.key, self.value)

        return self.build_topic("state", topic_host_name)

    def set_value(self, value):
        # Convert byte string values sent from MQTT to int bit values
        if value == b'1':
            value = 1
        elif value == b'0':
            value = 0

        self.value = value

    def mqtt_callback(self, value, topic_host_name):
        self.set_value(value)
        return self.build_topic("state", topic_host_name)

    def build_topic(self, action, topic_host_name):
        if self.topic != None:
            return self.topic.format(
                key=self.key, action=action, topicHostName=topic_host_name)
