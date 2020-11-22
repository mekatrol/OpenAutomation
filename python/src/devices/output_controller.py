from points.output import Output


class OutputController:
    def __init__(self, io_manager, mqtt, topic_host_name):
        self._io_manager = io_manager
        self._mqtt = mqtt
        self._topic_host_name = topic_host_name

        for key in io_manager.outputs:
            out = io_manager.outputs[key]
            topic = out.build_topic(
                topic_host_name=self._topic_host_name, action="set")

            if topic:
                mqtt.subscribe(topic, self.mqtt_callback, out)

    def mqtt_callback(self, value, out):
        # Translate known value types that an external MQTT publisher might provide (for safety)
        # Values 0 and 1 are the default that we accept
        if(value != 0 and value != 1):
            if value == b"0" or value == b"off":
                value = 0
            elif value == b"1" or value == b"on":
                value = 1
            else:
                # Turn off if value not recognised
                value = 0

        topic = out.mqtt_callback(value, self._topic_host_name)

        # If topic defeined then send value straight back
        if topic != None:
            # Convert value to MQTT b'off' or b'on'
            if out.value == 0:
                value = b'off'
            elif out.value == 1:
                value = b'on'
            
            self._mqtt.publish(topic, value)

    def tick(self):
        for key in self._io_manager.outputs:
            out = self._io_manager.outputs[key]

            # Do not call tick on pins dedicated to other functions (eg pins that are dedicated to a shift register)
            if out.key in self._io_manager.dedicated_outputs:
                continue

            topic = out.tick(self._topic_host_name)

            if topic != None:
                # Publish value if topic defined
                self._mqtt.publish(topic, out.value)
