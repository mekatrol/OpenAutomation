
class Output:
    def __init__(self, output_def, io_manager, mqtt, topic_host_name):
        self.key = output_def["key"]
        self._output_def = output_def
        self._io_manager = io_manager
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

        value = 0
        if self.value == b"on":
            value = 1

        # Use IO manager to set ouput (GPIO or SR)
        self._io_manager.output(self.key, value)
        
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
                key=self.key, action=action, topicHostName=topic_host_name)


class OutputController:
    def __init__(self, io_manager, mqtt, topic_host_name):
        self._io_manager = io_manager
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
        for out in self._outputs:
            # Do not call tick on pins dedicated to other functions (eg pins that are dedicated to a shift register)
            if out.key in self._io_manager.dedicated_outputs:
                continue
            
            out.tick(self._mqtt)        
