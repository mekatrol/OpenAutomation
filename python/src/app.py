import json
import time
import os.path
from host.monitor import Monitor
from communication.mqtt import Mqtt

CONFIG_FILE_NAME = "config.json"


def main():
    # Make sure config file exists
    if not os.path.isfile(CONFIG_FILE_NAME):
        print("Configuration file '%s' does not exist." % CONFIG_FILE_NAME)
        return

    # Read the configuration file
    config = None

    try:
        with open(CONFIG_FILE_NAME) as f:
            config = json.load(f)
    except Exception as ex:
        print("Error: " + ex.output)
        return

    # Default to 3 seconds
    loopSleepTime = 3

    # Override with config value (if defined)
    if "app" in config and "loopSleepTime" in config["app"]:
        loopSleepTime = config["app"]["loopSleepTime"]

    # Create the MQTT instance
    mqtt = Mqtt(config)
    mqtt.connect()

    host_monitor = Monitor(config, mqtt)

    try:
        while True:
            host_monitor.tick()
            time.sleep(loopSleepTime)

    except KeyboardInterrupt:
        pass

    finally:
        mqtt.close()


if __name__ == "__main__":
    main()
