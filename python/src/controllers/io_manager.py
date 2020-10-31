import RPi.GPIO as GPIO
from helpers.dictionary_helper import DictionaryHelper
from controllers.shift_register import ShiftRegister
from devices.output_controller import OutputController
from devices.input import Input
from devices.output import Output


class IoManager:
    def __init__(self, config, mqtt, topic_host_name):
        # If no IO section then don't process further
        if not "io" in config:
            return

        # Get IO config
        io_conf = config["io"]

        # Get GPIO pin numbering mode
        if not "pinNumberingMode" in io_conf:
            # Need pin numbering mode to be able to use IO
            raise Exception(
                "The pin numbering mode has not been defined (using the 'pinNumberingMode' property (valid values: 'BCM', 'BOARD')")
        pin_numbering_mode = io_conf["pinNumberingMode"]

        # Set GPIO pin numbering mode
        if pin_numbering_mode == "BCM":
            GPIO.setmode(GPIO.BCM)
        elif pin_numbering_mode == "BOARD":
            GPIO.setmode(GPIO.BOARD)
        else:
            raise Exception(
                "pinNumberingMode value must be set to 'BCM' or 'BOARD'")

        # Dedicated IO pins are those GPIO pins that a dedicated to
        # another purpose (eg shift register control pin). They should not
        # be controllable as a general IO pin
        self.dedicated_inputs = {}
        self.dedicated_outputs = {}

        # Initialise inputs
        if "inputs" in io_conf:
            self.__init_inputs(io_conf["inputs"])

        # Initialise outputs
        if "outputs" in io_conf:
            self.__init_outputs(io_conf["outputs"])

        # Initialise shift registers
        if "shiftRegisters" in io_conf:
            self.__init_shift_registers(io_conf["shiftRegisters"])

        self._mqtt = mqtt
        self._topic_host_name = topic_host_name
        self._output_controller = OutputController(self, mqtt, topic_host_name)


    def input(self, key):
        # To read an input then the input config must exist
        if not key in self.inputs:
            raise Exception(f"Invalid input key '{key}'")

        # Use GPIO to return value based in input config
        return GPIO.input(self.inputs[key].pin)

    def output(self, key, value):
        # To write an ouput then the output config must exist
        if not key in self.outputs:
            raise Exception(f"Invalid output key '{key}'")

        # Get the output config
        out = self.outputs[key]

        # If the output is a GPIO type then set output value using
        # GPIO library
        if out.device_type == "GPIO":
            GPIO.output(out.pin, value)

        # If the output is a shift register output for a shift register then
        # update shift register output value
        elif out.device_type == "SR":
            # Get the referenced shift register
            shift_register_def = self._shift_register_defs[out.shift_register_key]

            # Get the number of output bits per device
            outputs_per_device = shift_register_def["outputs_per_device"]

            # Get the shift register pin number, this is the output number
            # from 1 to n where n is the max number of outputs for the
            # total number of devices.
            # For example, if there are two 74HC595 devices chained then
            # the total number of outputs will be 16 (2 devices x 8 outputs each device)
            shift_register_pin = out.pin

            # Get the device output number for the pin. Given 8 pins
            # per device then the device number is simply: floor('pin number' / 8).
            # NOTE: python int function 'floors' the number automatically
            device = int(shift_register_pin / outputs_per_device)

            # Get the output pin number for the device that the pin belongs to.
            # This is simply the pin number modulo 8 (for 8 bits per device)
            # For example, if there are two 74HC595 devices chained then
            # Shift register pin 1 will be output pin 1 on the first device, and
            # shift register pin 8 will aldo be pin 1, but on the second device
            device_pin = shift_register_pin % outputs_per_device

            # Determine the bit position for the device pin number
            # For example:
            #   pin 1 has the shifted binary value 0b0000001
            #   pin 8 has the shifted binary value 0b1000000
            pin_shifted_value = 1 << (device_pin - 1)

            # If the value of the output is 1 (on) then we OR the shifted bit
            # with the device output value, else we AND the complement shifted bit value
            # For example, for pin 1 we would:
            #   for an 'on':  device_output_value |= 0b00000001
            #   for an 'off': device_output_value &= 0b11111110
            # For example, for pin 2 we would:
            #   for an 'on':  device_output_value |= 0b00000010
            #   for an 'off': device_output_value &= 0b11111101
            if value == 1:
                shift_register_def["output_values"][device] |= pin_shifted_value
            else:
                shift_register_def["output_values"][device] &= ~pin_shifted_value

        # Not a valid type?
        else:
            out_type = out.device_type
            raise Exception(
                f"Invalid output type '{out_type}' for output with key '{key}'")

    def tick(self, mqtt):

        self._process_inputs()
        self._process_outputs()
        self._shift_values()

    def _process_inputs(self):
        for key in self.inputs:
            # Do not call tick on pins dedicated to other functions (eg pins that are dedicated to SPI device)
            if key in self.dedicated_inputs:
                continue

            # Process input
            self.inputs[key].tick(self._mqtt, self._topic_host_name)


    def _process_outputs(self):
        self._output_controller.tick()

    def _shift_values(self):
        # For each shift register, update its ouput (shift its values)
        for key in self._shift_register_defs:
            # Get the shift register definition
            shift_register_def = self._shift_register_defs[key]

            # Get the shift register instance
            shift_register = self._shift_registers[key]

            # Get the output values for the shift register
            outputs = bytes(shift_register_def["output_values"])

            # Shift values to output shift register
            shift_register.clear_latch()
            shift_register.shift_bytes(outputs)
            shift_register.set_latch()

    def __init_inputs(self, inputs):
        # Create input definition dictionary
        self.inputs = {}

        # Iterate input configurations
        for input_config in inputs:
            config = DictionaryHelper(input_config, "input")

            # Get property values
            key = config.get_str("key", False, None)
            device_type = config.get_str("deviceType", True, "GPIO")
            pud = config.get_str("pud", True, "PUD_OFF")
            pin = config.get_int("pin", False, None, 0, 100)
            name = config.get_str("name", True, None)
            topic = config.get_str("topic", True, None)
            interval = config.get_int("interval", True, 3, 1, None)

            # Can't add same key twice
            if key in self.inputs:
                raise Exception("Input with key '{key}' already defined")

            # Convert pull_up_down definition
            if pud == "PUD_UP":
                pud = GPIO.PUD_UP

            elif pud == "PUD_DOWN":
                pud = GPIO.PUD_DOWN

            elif pud != "PUD_OFF":
                raise Exception("Input invalid 'pud' property value")

            # Create the definition
            inp = Input(self, key, name, device_type,
                        pin, pud, topic, interval)

            # Add to input dictionary
            self.inputs[key] = inp

            # If a GPIO pin then configure hardware
            if device_type == "GPIO":
                GPIO.setup(inp.pin, GPIO.IN, pull_up_down=pud)

    def __init_outputs(self, outputs):
        # Create output definition dictionary
        self.outputs = {}

        # Iterate output configurations
        for output_config in outputs:
            config = DictionaryHelper(output_config, "input")

            # Get property values from config
            key = config.get_str("key", False, None)
            device_type = config.get_str("deviceType", True, "GPIO")
            pin = config.get_int("pin", False, None, 0, 100)
            name = config.get_str("name", True, None)
            topic = config.get_str("topic", True, None)
            interval = config.get_int("interval", True, 3, 1, None)
            shift_register_key = config.get_str("shiftRegisterKey", True, None)

            # Can't add same key twice
            if key in self.outputs:
                raise Exception("Output with key '{key}' already defined")

            # Validate type
            if device_type != "GPIO" and device_type != "SR":
                raise Exception("Output invalid 'type' property value")

            # If shift register output them make sure shift register key defined
            if device_type == "SR":
                if shift_register_key == None:
                    raise Exception(
                        f"shiftRegisterkey property must be defined for output with key '{key}'")

            # Create the definition
            out = Output(self, key, name, device_type, pin, topic,
                         interval, shift_register_key)

            # Add to output dictionary
            self.outputs[key] = out

            # If a GPIO pin then configure hardware
            if device_type == "GPIO":
                GPIO.setup(out.pin, GPIO.OUT)

    def __init_shift_registers(self, shift_registers):
        # Create shift register definition dictionary
        self._shift_register_defs = {}

        # Create shift register instance dictionary
        self._shift_registers = {}

        # Iterate shift register configurations
        for shift_register_config in shift_registers:
            config = DictionaryHelper(shift_register_config, "input")

            # Get property values from config
            key = config.get_str("key", False, None)
            name = config.get_str("name", True, None)
            shift_register_key = config.get_str("shiftRegisterKey", True, None)
            devices = config.get_int("devices", False, 1)
            outputs_per_device = config.get_int(
                "outputsPerDevice", True, min_value=8)
            data = config.get_str("data", False)
            clock = config.get_str("clock", False)
            latch = config.get_str("latch", False)
            oe = config.get_str("oe", True)
            clear = config.get_str("clear", True)
            interval = config.get_int("interval", True, default=3, min_value=1)

            # Create array to hold 8 bit values for each device
            output_values = [0] * devices

            # Add shift register pin keys to dedicated pin set
            self.dedicated_outputs[data] = True
            self.dedicated_outputs[clock] = True
            self.dedicated_outputs[data] = True
            self.dedicated_outputs[latch] = True

            if oe:
                self.dedicated_outputs[oe] = True

            if clear:
                self.dedicated_outputs[clear] = True

            shift_register_def = {
                "key": key,
                "name": name,
                "devices": devices,
                "outputs_per_device": outputs_per_device,
                "data": data,
                "clock": clock,
                "latch": latch,
                "oe": oe,
                "clear": clear,
                "output_values": output_values
            }

            # Add definition
            self._shift_register_defs[key] = shift_register_def

            # Create and add shift register
            shift_register = ShiftRegister(self, shift_register_def)
            self._shift_registers[key] = shift_register
