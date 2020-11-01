import paho.mqtt.client as mqtt


def on_connect(client, userdata, flags, rc):
    # userdata is set to the Mqtt class instance
    if rc == 0:
        userdata.connected = True
    else:
        userdata.connected = False


def on_message(client, userdata, msg):
    if msg.topic in userdata.subscribe_callbacks:
        callback_data = userdata.subscribe_callbacks[msg.topic]

        callback = callback_data["callback"]
        data = callback_data["data"]

        callback(msg.payload, data)


class Mqtt:
    def __init__(self, config):
        # Connection credentials (if needed)
        self.mqtt_username = None
        self.mqtt_password = None
        self.mqtt_broker_host = None
        self.mqtt_broker_port = 1883
        self.mqtt_keep_alive = 60

        self.connected = False
        self.client = mqtt.Client(userdata=self)
        self.subscribe_callbacks = {}

        self.__init(config)

    def __init(self, config):
        # Wire up events
        self.client.on_connect = on_connect
        self.client.on_message = on_message

        broker_config = config.get_config_section("broker")

        self.mqtt_broker_host = broker_config.get_str("host", False, default=None)
        self.mqtt_broker_port = broker_config.get_int("port", False, default=8123)
        self.mqtt_keep_alive = broker_config.get_int("keep_alive", False, default=60)
        self.mqtt_username = broker_config.get_str("username", True, default=None)
        self.mqtt_password = broker_config.get_str("password", True, default=None)

        if self.mqtt_username != None:
            self.client.username_pw_set(
                self.mqtt_username,
                password=self.mqtt_password)

    def close(self):
        self.client.disconnect()

    def connect(self):
        self.client.connect(self.mqtt_broker_host, self.mqtt_broker_port,
                            self.mqtt_keep_alive)

    def publish(self, topic, value):
        self.client.publish(topic, value)

    def subscribe(self, topic, callback, data):
        if topic != None and callback != None:
            self.client.subscribe(topic)
            self.subscribe_callbacks[topic] = {
                "callback": callback,
                "data": data
            }

    def loop(self, timeout):
        self.client.loop(timeout=timeout, max_packets=1)
