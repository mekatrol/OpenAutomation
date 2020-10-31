from devices.output import Output


class OutputController:
    def __init__(self, io_manager, mqtt, topic_host_name):
        self._io_manager = io_manager
        self._mqtt = mqtt
        self._topic_host_name = topic_host_name

        for key in io_manager.outputs:
            out = io_manager.outputs[key]
            topic = out.build_topic("set", self._topic_host_name)

            if topic:
                mqtt.subscribe(topic, self.mqtt_callback, out)

    def mqtt_callback(self, value, out):
        topic = out.mqtt_callback(value, self._topic_host_name)

        if topic != None:
            # Send value straight back if topic defined
            self._mqtt.publish(topic, out.value)

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
