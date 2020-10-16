import json
import time
import os.path
import socket
from host.monitor import Monitor
from communication.mqtt import Mqtt
from controllers.shift_register import ShiftRegister
from devices.output_controller import OutputController

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

    device_count = None
    data_pin = None
    clock_pin = None
    latch_pin = None
    oe_pin = None
    clear_pin = None
    zone_config = {}

    if "irrigation" in config:
        if "shiftRegister" in config["irrigation"]:
            shift_register_config = config["irrigation"]["shiftRegister"]
            if "data" in shift_register_config:
                data_pin = shift_register_config["data"]
            if "clock" in shift_register_config:
                clock_pin = shift_register_config["clock"]
            if "latch" in shift_register_config:
                latch_pin = shift_register_config["latch"]
            if "outputEnable" in shift_register_config:
                oe_pin = shift_register_config["outputEnable"]
            if "clear" in shift_register_config:
                clear_pin = shift_register_config["clear"]

        if "zones" in config["irrigation"]:
            zone_config = config["irrigation"]["zones"]

            # Get the number zones
            zone_count = len(zone_config)

            # There are 8 bits per shift register device
            device_count = int(zone_count / 8)
            if (zone_count - (device_count * 8)) % 8 > 0:
                device_count += 1

    # Only initalise output controller if device count and minimum pins defined has value
    if device_count != None and data_pin != None and clock_pin != None and latch_pin != None:
        shift_register = ShiftRegister(
            device_count, data_pin, clock_pin, latch_pin, oe_pin, clear_pin)
        output_controller = OutputController(
            config, shift_register, mqtt, topic_host_name)

    try:
        while True:
            # Process MQTT loop
            mqtt.loop(100)

            # Process host monitor tick
            host_monitor.tick()

            # Process output controller tick
            output_controller.tick()

            # Sleep a bit
            time.sleep(loopSleepTime)

    except KeyboardInterrupt:
        pass

    finally:
        mqtt.close()
        shift_register.close()


if __name__ == "__main__":
    main()
