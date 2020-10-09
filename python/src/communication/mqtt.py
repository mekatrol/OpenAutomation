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


class Mqtt:
    def __init__(self):
        # Connection credentials (if needed)
        self.mqtt_username = None
        self.mqtt_password = None
        self.mqtt_broker_host = None
        self.mqtt_broker_port = 1883
        self.mqtt_keep_alive = 60

        self.connected = False
        self.client = mqtt.Client(userdata=self)

    def init(self, config):
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
                    self. mqtt_password = config["mqtt"]["broker"]["password"]

        if not self.mqtt_username == None:
            self.client.username_pw_set(
                self. mqtt_username,
                password=self.mqtt_password)

    def close(self):
        self.client.disconnect()

    def connect(self):
        self.client.connect(self.mqtt_broker_host, self.mqtt_broker_port,
                            self.mqtt_keep_alive)

    def publish(self, topic, value):
        self.client.publish(topic, value)
