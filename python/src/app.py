import json
import time
import os.path
from host.rpi import *
from communication.mqtt import Mqqt

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

    mqqt = Mqqt()

    mqqt.init(config)
    mqqt.connect()

    try:
        while True:
            temp = host_get_cpu_temp()
            mqqt.publish("irrigation/host/cpu_temp", temp)

            temp = host_get_gpu_temp()
            mqqt.publish("irrigation/host/gpu_temp", temp)

            clock = host_get_cpu_clock()
            mqqt.publish("irrigation/host/cpu_clock", clock)

            status = host_get_throttled_status()
            mqqt.publish("irrigation/host/throttled_status", status)

            time.sleep(3)

    except KeyboardInterrupt:
        pass

    finally:
        mqqt.close()


if __name__ == "__main__":
    main()
