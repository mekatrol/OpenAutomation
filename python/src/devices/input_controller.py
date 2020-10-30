class Input:
    def __init__(self, input_def, io_manager, mqtt, topic_host_name):
        self._input_def = input_def
        self._io_manager = io_manager
        self._mqtt = mqtt
        self._topic_host_name = topic_host_name
        self._interval = 1

        if "interval" in input_def:
            self._interval = input_def["interval"]

        self._count_down = self._interval

    def tick(self):
        # Use interval if defined
        if self._interval != None:

            # Decrement count down
            self._count_down -= 1

            # Count down not reached zero (interval incomplete)?
            if self._count_down > 0:
                return

            # Reset countdown from interval
            self._count_down = self._interval

        key = self._input_def["key"]
        name = self._input_def["name"]
        value = self._io_manager.input(key)
        topic_template = self._input_def["topic"]

        if topic_template != None:
            topic_built = topic_template.format(
                key=key, name=name, topicHostName=self._topic_host_name)
            self._mqtt.publish(topic_built, value)


class InputController:
    def __init__(self, io_manager, mqtt, topic_host_name):
        self._io_manager = io_manager
        self._mqtt = mqtt
        self._topic_host_name = topic_host_name

        # Create the monitor items from the monitor config
        self._inputs = [Input(io_manager.inputs[key], io_manager, mqtt, topic_host_name)
                        for key in io_manager.inputs]

    def tick(self):
        for inp in self._inputs:
            inp.tick()
