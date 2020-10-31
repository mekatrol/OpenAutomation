from points.point import IoPoint

class Input(IoPoint):
    def __init__(self, io_manager, key, name, description, device_type, pin, pud, topic, interval):
        super(self.__class__, self).__init__(key, name, description, topic, interval)


        self.device_type = device_type
        self.pin = pin
        self.pud = pud
        self._io_manager = io_manager
        
        # Start countdown at interval
        self._count_down = self.interval

    def tick(self, mqtt, topic_host_name):
        # Use interval if defined
        if self.interval != None:

            # Decrement count down
            self._count_down -= 1

            # Count down not reached zero (interval incomplete)?
            if self._count_down > 0:
                return

            # Reset countdown from interval
            self._count_down = self.interval

        # Get the current value
        value = self._io_manager.input(self.key)

        # Get topic (if any)
        topic_template = self.topic

        # If a topic is defined then we publish the value via MQTT
        if topic_template != None:
            topic_built = topic_template.format(
                key=self.key, name=self.name, topicHostName=topic_host_name)
            
            mqtt.publish(topic_built, value)