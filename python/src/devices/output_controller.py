
class Output:
    def __init__(self, output_def, io_controller, mqtt, topic_host_name):
        self._output_def = output_def
        self._io_controller = io_controller
        self._mqtt = mqtt
        self._topic_host_name = topic_host_name

        self._interval = 1
        if "interval" in output_def:
            self._interval = output_def["interval"]

        self.value = "off"
        self._count_down = self._interval

    def tick(self, mqtt):
        # Use interval if defined
        if self._interval != None:

            # Decrement count down
            self._count_down -= 1

            # Count down not reached zero (interval incomplete)?
            if self._count_down > 0:
                return

            # Reset countdown from interval
            self._count_down = self._interval

            topic = self.build_topic("state", self._topic_host_name)
            if topic:
                self._mqtt.publish(topic, self.value)

    def callback(self, value):
        self.value = value

        # Send state straight back
        topic = self.build_topic("state", self._topic_host_name)
        if topic:
            self._mqtt.publish(topic, self.value)

    def build_topic(self, action, topic_host_name):
        if "topic" in self._output_def and self._output_def["topic"] != None:
            return self._output_def["topic"].format(
                key=self._output_def["key"], action=action, topicHostName=topic_host_name)


class OutputController:
    def __init__(self, io_manager, mqtt, topic_host_name):
        self.io_manager = io_manager
        self._mqtt = mqtt
        self._topic_host_name = topic_host_name

        # Create output handlers
        self._outputs = [Output(io_manager.outputs[key], io_manager, mqtt, self._topic_host_name)
                         for key in io_manager.outputs]

        for out in self._outputs:
            topic = out.build_topic("set", self._topic_host_name)

            if topic:
                mqtt.subscribe(topic, out.callback)

    def tick(self):
        # Enumerate the zones, update state and calculate shift bit value
        # value = 0
        # shift = 1

        for out in self._outputs:
            out.tick(self._mqtt)
        #     if out.value == b"on":
        #         value |= shift

        #     shift <<= 1

        # # Convert to byte array containing the number of devices
        # # using little endian ordering for the array
        # bytes = value.to_bytes(self._device_count, 'big')

        # # Shift bit values to output shift register
        # self._shift_register.clear_latch()
        # self._shift_register.shift_bytes(bytes)
        # self._shift_register.set_latch()
