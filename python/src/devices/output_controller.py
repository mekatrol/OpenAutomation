
class Zone:
    def __init__(self, zone_config, mqtt, topic_host_name):
        self.key = zone_config["key"]
        self.name = zone_config["name"]
        self.topic = zone_config["topic"]
        self._topic_host_name = topic_host_name
        self._mqtt = mqtt

        self._interval = 1
        if "interval" in zone_config:
            self._interval = zone_config["interval"]
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
        mqtt.publish(topic, self.value)

    def callback(self, value):
        self.value = value

        # Send state straight back
        topic = self.build_topic("state", self._topic_host_name)
        self._mqtt.publish(topic, self.value)

    def build_topic(self, action, topic_host_name):
        return self.topic.format(
            key=self.key, action=action, topicHostName=topic_host_name)


class OutputController:
    def __init__(self, config, shift_register, device_count, mqtt, topic_host_name):
        if not "mqtt" in config or not "irrigation" in config or mqtt == None:
            # Nothing to control
            return

        # Keep references to other devices
        self._shift_register = shift_register
        self._mqtt = mqtt

        # Keep device count
        self._device_count = device_count

        # Keep topic host name
        self._topic_host_name = topic_host_name

        # Init array of zones
        self._zones = []

        if "zones" in config["irrigation"]:
            zone_config = config["irrigation"]["zones"]

            # Create the monitor items from the monitor config
            self._zones = [Zone(z, mqtt, self._topic_host_name)
                           for z in zone_config]

            for zone in self._zones:
                mqtt.subscribe(zone.build_topic(
                    "set", self._topic_host_name), zone.callback)

    def tick(self):
        # Enumerate the zones, update state and calculate shift bit value
        value = 0
        shift = 1

        for zone in self._zones:
            zone.tick(self._mqtt)
            if zone.value == b"on":
                value |= shift
            
            shift <<= 1

        # Convert to byte array containing the number of devices
        # using little endian ordering for the array
        bytes = value.to_bytes(self._device_count, 'big')

        # Shift bit values to output shift register
        self._shift_register.clear_latch()
        self._shift_register.shift_bytes(bytes)
        self._shift_register.set_latch()
