import glob
import json
import time
import os.path
import socket

import RPi.GPIO as GPIO

from host.monitor import Monitor
from communication.mqtt import Mqtt
from controllers.io_manager import IoManager
from controllers.shift_register import ShiftRegister
from devices.output_controller import OutputController
from devices.input_controller import InputController

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

    io_manager = IoManager(config)

    input_controller = InputController(io_manager, mqtt, topic_host_name)


    # Create temp sensor
    # base_dir = '/sys/bus/w1/devices/'
    # devices = glob.glob(base_dir + '28*')
    # device_folder = devices[0]
    # device_file_name = device_folder + '/w1_slave'

    # Only initalise output controller if shift register defined
    if "sr1" in io_manager.shift_registers:
        shift_register_def = io_manager.shift_registers["sr1"]

        shift_register = ShiftRegister(io_manager, shift_register_def)
        
        output_controller = OutputController(
            config, shift_register, shift_register_def["devices"], mqtt, topic_host_name)

    try:
        x = 0
        while True:
            # Process MQTT loop
            mqtt.loop(100)

            # Process host monitor tick
            host_monitor.tick()

            # Process output controller tick
            output_controller.tick()

            # Process input controller tick
            input_controller.tick()

            # Sleep a bit
            time.sleep(loopSleepTime)

    except KeyboardInterrupt:
        pass

    finally:
        mqtt.close()
        shift_register.close()


if __name__ == "__main__":
    main()
