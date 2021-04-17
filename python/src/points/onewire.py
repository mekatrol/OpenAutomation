from points.point import IoPoint


class OneWire(IoPoint):
    def __init__(self, io_manager, key, name, description, file, value, topic, interval, mqtt_publish_interval):
        super().__init__(
            key, name, description, value, False, topic, interval, mqtt_publish_interval)
        self.file = "/sys/bus/w1/devices/" + file + "/w1_slave"

    def tick(self, topic_host_name):
        # Has any defined interval expired
        if not super().interval_expired():
            # No, then do no processing this tick
            return

        temp_c = self.__read_temp()

        if(temp_c != None):
            self.value = temp_c

        if self.mqtt_publish_tick(topic_host_name):
            # Return built topic (if topic template defined)
            return super().build_topic(topic_host_name, action="state")

        return None

    def __read_temp_raw(self):
        f = open(self.file, 'r')
        lines = f.readlines()
        f.close()
        return lines

    def __read_temp(self):
        lines = self.__read_temp_raw()
        if lines[0].strip()[-3:] != 'YES':
            # CRC check failure (bad read)
            return None

        equals_pos = lines[1].find('t=')
        if equals_pos != -1:
            temp_string = lines[1][equals_pos+2:]
            temp_c = float(temp_string) / 1000.0
            return temp_c

        # No equals sign found (bad file)
        return None
