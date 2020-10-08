import paho.mqtt.client as mqtt


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        userdata.connected = true
    else:
        print("Bad connect code: " + str(rc))
        userdata.connected = False

        # Don't bother subscribing if connection failed
        return

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    userdata.client.subscribe("irrigation/status")


def on_message(client, userdata, msg):
    print(msg.topic + " " + str(msg.payload))


class Mqqt:
    def __init__(self):
        # Connection credentials (if needed)
        self.mqtt_username = None
        self.mqtt_password = None
        self.mqtt_host = None
        self.mqtt_port = 1883
        self.mqtt_keep_alive = 60

        self.connected = False
        self.client = mqtt.Client(userdata=self)

    def init(self, config):
        # Wire up events
        self.client.on_connect = on_connect
        self.client.on_message = on_message

        # Get username and password (if configured)
        if "mqqt" in config:
            if "host" in config["mqqt"]:
                self.mqtt_host = config["mqqt"]["host"]

            if "port" in config["mqqt"]:
                self.mqtt_port = config["mqqt"]["port"]

            if "keep_alive" in config["mqqt"]:
                self.mqtt_keep_alive = config["mqqt"]["keep_alive"]

            if "username" in config["mqqt"]:
                self.mqtt_username = config["mqqt"]["username"]

            if "password" in config["mqqt"]:
                self. mqtt_password = config["mqqt"]["password"]

        if not self.mqtt_username == None:
            self.client.username_pw_set(
                self. mqtt_username,
                password=self.mqtt_password)

    def close(self):
        self.client.disconnect()

    def connect(self):
        self.client.connect(self.mqtt_host, self.mqtt_port,
                            self.mqtt_keep_alive)

    def publish(self, topic, value):
        self.client.publish(topic, value)
