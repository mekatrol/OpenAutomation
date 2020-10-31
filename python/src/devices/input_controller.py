from devices.input import Input

class InputController:
    def __init__(self, io_manager, mqtt, topic_host_name):
        self._io_manager = io_manager
        self._mqtt = mqtt
        self._topic_host_name = topic_host_name

    def tick(self):
        for inp in self._inputs:
            # Do not call tick on pins dedicated to other functions (eg pins that are dedicated to SPI device)
            if inp.key in self._io_manager.dedicated_inputs:
                continue

            inp.tick()
