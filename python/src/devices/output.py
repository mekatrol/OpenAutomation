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

        self.value = "off"
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

        value = 0
        if self.value == b"on":
            value = 1

        # Use IO manager to set ouput (GPIO or SR)
        self._io_manager.output(self.key, value)

        return self.build_topic("state", topic_host_name)

    def mqtt_callback(self, value, topic_host_name):
        self.value = value

        return self.build_topic("state", topic_host_name)

    def build_topic(self, action, topic_host_name):
        if self.topic != None:
            return self.topic.format(
                key=self.key, action=action, topicHostName=topic_host_name)
