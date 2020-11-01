import glob
import json
import time
import os.path
import socket

import RPi.GPIO as GPIO

from communication.mqtt import Mqtt
from devices.host_controller import HostController
from devices.io_manager import IoManager
from devices.script_manager import ScriptManager
from helpers.dictionary_helper import DictionaryHelper

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
            config = DictionaryHelper(json.load(f), "config")
    except Exception as ex:
        print("Error: " + ex.output)
        return

    # Get app section
    app_config = config.get_config_section("app")

    # Default to 3 seconds
    loopSleepTime = app_config.get_float(
        "loopSleepTime", False, default=0.2, min_value=0.1)

    # Get mqtt section
    mqtt_config = config.get_config_section("mqtt")
    topic_host_name = mqtt_config.get_str("topicHostName", True, default=None)
    if topic_host_name == None:
        topic_host_name = socket.gethostname()

    # Create the MQTT instance
    mqtt = Mqtt(mqtt_config)
    mqtt.connect()

    io_config = config.get_config_section("io")    
    if io_config != None:
        io_manager = IoManager(io_config, mqtt, topic_host_name)

    host_controller = None
    monitors = io_config.get_any("monitors")    
    if monitors != None:
        host_controller = HostController(monitors, mqtt, topic_host_name)

    script_manager = None    
    scripts_path = app_config.get_str("scriptsPath", True, default=None)

    if scripts_path != None:
        script_manager = ScriptManager()
        script_manager.load_scripts(scripts_path)

    # Create temp sensor
    # base_dir = '/sys/bus/w1/devices/'
    # devices = glob.glob(base_dir + '28*')
    # device_folder = devices[0]
    # device_file_name = device_folder + '/w1_slave'

    try:
        mister_sw_last_tick = 0
        light_sw_last_tick = 0

        while True:

            # Process MQTT loop
            mqtt.loop(10)

            # Process host monitor tick
            if host_controller != None:
                host_controller.tick()

            # Process IO
            io_manager.tick(mqtt)

            # Process scripts
            if script_manager != None:
                script_manager.tick()

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
