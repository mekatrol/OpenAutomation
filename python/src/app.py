import glob
import json
import time
import os.path
import socket

import RPi.GPIO as GPIO

from host.monitor import Monitor
from communication.mqtt import Mqtt
from controllers.io_manager import IoManager

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

    # Read the host name if defined (can be used for string formatting)
    if "mqtt" in config and "topicHostName" in config["mqtt"]:
        topic_host_name = config["mqtt"]["topicHostName"]
    else:
        topic_host_name = socket.gethostname()

    # Create the MQTT instance
    mqtt = Mqtt(config)
    mqtt.connect()

    host_monitor = Monitor(config, mqtt, topic_host_name)

    io_manager = IoManager(config, mqtt, topic_host_name)

    # Create temp sensor
    # base_dir = '/sys/bus/w1/devices/'
    # devices = glob.glob(base_dir + '28*')
    # device_folder = devices[0]
    # device_file_name = device_folder + '/w1_slave'

    try:
        mister_sw_last_tick = 0
        light_sw_last_tick = 0
        i = 0
        while True:
            i += 1
            print(i)

            # Process MQTT loop
            mqtt.loop(10)

            # Process host monitor tick
            host_monitor.tick()

            # Process IO
            io_manager.tick(mqtt)

            mister_sw = io_manager.input("mister_switch")
            if mister_sw and mister_sw != mister_sw_last_tick:
                io_manager.toggle_output("sr1_out1")
            mister_sw_last_tick = mister_sw            

            light_sw = io_manager.input("light_switch")
            if light_sw and light_sw != light_sw_last_tick:
                io_manager.toggle_output("sr1_out2")
            light_sw_last_tick = light_sw            

            # Sleep a bit
            time.sleep(loopSleepTime)

    except KeyboardInterrupt:
        pass

    finally:
        mqtt.close()


if __name__ == "__main__":
    main()
