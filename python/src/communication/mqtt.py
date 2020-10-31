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

        # Get username and password (if configured)
        if "mqtt" in config:
            if "broker" in config["mqtt"]:
                if "host" in config["mqtt"]["broker"]:
                    self.mqtt_broker_host = config["mqtt"]["broker"]["host"]

                if "port" in config["mqtt"]["broker"]:
                    self.mqtt_broker_port = config["mqtt"]["broker"]["port"]

                if "keep_alive" in config["mqtt"]["broker"]:
                    self.mqtt_keep_alive = config["mqtt"]["broker"]["keep_alive"]

                if "username" in config["mqtt"]["broker"]:
                    self.mqtt_username = config["mqtt"]["broker"]["username"]

                if "password" in config["mqtt"]["broker"]:
                    self.mqtt_password = config["mqtt"]["broker"]["password"]

        if not self.mqtt_username == None:
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
