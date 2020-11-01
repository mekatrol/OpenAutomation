import RPi.GPIO as GPIO
from helpers.dictionary_helper import DictionaryHelper
from devices.shift_register import ShiftRegister
from devices.output_controller import OutputController
from points.input import Input
from points.output import Output
from points.virtual import Virtual


class IoManager:
    def __init__(self, config, mqtt, topic_host_name):
        # If no IO section then don't process further
        if not config:
            return

        # Get GPIO pin numbering mode
        pin_numbering_mode = config.get_str("gpioPinNumberingMode", True, default="BCM")

        # Set GPIO pin numbering mode
        if pin_numbering_mode == "BCM":
            GPIO.setmode(GPIO.BCM)
        elif pin_numbering_mode == "BOARD":
            GPIO.setmode(GPIO.BOARD)
        else:
            raise Exception(
                "gpioPinNumberingMode value must be set to 'BCM' or 'BOARD'")

        # Dedicated IO pins are those GPIO pins that a dedicated to
        # another purpose (eg shift register control pin). They should not
        # be controllable as a general IO pin
        self.dedicated_inputs = {}
        self.dedicated_outputs = {}

        # Initialise inputs
        inputs = config.get_any("inputs")
        if inputs != None:
            self.__init_inputs(inputs)

        # Initialise outputs
        outputs = config.get_any("outputs")
        if outputs != None:
            self.__init_outputs(outputs)

        # Initialise virtual points
        virtuals = config.get_any("virtuals")
        if virtuals != None:
            self.__init_virtuals(virtuals)

        # Initialise shift registers
        shift_registers = config.get_any("shiftRegisters")
        if shift_registers != None:
            self.__init_shift_registers(shift_registers)

        self._mqtt = mqtt
        self._topic_host_name = topic_host_name
        self._output_controller = OutputController(self, mqtt, topic_host_name)

    def input(self, key):
        # To read an input then the input config must exist
        if not key in self.inputs:
            raise Exception(f"Invalid input key '{key}'")

        # Use GPIO to return value based in input config
        return GPIO.input(self.inputs[key].pin)

    def toggle_output(self, key):
        # To write an ouput then the output config must exist
        if not key in self.outputs:
            raise Exception(f"Invalid output key '{key}'")

        # Get the output
        out = self.outputs[key]

        if out.value == 1:
            out.value = 0
        else:
            out.value = 1

    def output(self, key, value):
        # To write an ouput then the output config must exist
        if not key in self.outputs:
            raise Exception(f"Invalid output key '{key}'")

        # Get the output
        out = self.outputs[key]
        out.set_value(value)

        # If the output is a GPIO type then set output value using
        # GPIO library
        if out.device_type == "GPIO":
            GPIO.output(out.pin, value)

        # If the output is a shift register output for a shift register then
        # update shift register output value
        elif out.device_type == "SR":
            # Get the referenced shift register
            shift_register = self._shift_registers[out.shift_register_key]

            # Get the number of output bits per device
            outputs_per_device = shift_register.outputs_per_device

            # Get the shift register pin number, this is the output number
            # from 1 to n where n is the max number of outputs for the
            # total number of devices.
            # For example, if there are two 74HC595 devices chained then
            # the total number of outputs will be 16 (2 devices x 8 outputs each device)
            # Subtract 1 so that shift and modulo work
            # (ie pin 1 will shift zero bits, and pin 8 will shift 7 bits and will still be on device 1)
            shift_register_pin = (out.pin - 1)

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
            pin_shifted_value = 1 << device_pin

            # If the value of the output is 1 (on) then we OR the shifted bit
            # with the device output value, else we AND the complement shifted bit value
            # For example, for pin 1 we would:
            #   for a '1':  device_output_value |= 0b00000001
            #   for a '0': device_output_value &= 0b11111110
            # For example, for pin 2 we would:
            #   for a '1':  device_output_value |= 0b00000010
            #   for a '0': device_output_value &= 0b11111101
            if value == 1:
                shift_register.output_values[device] |= pin_shifted_value
            else:
                shift_register.output_values[device] &= ~pin_shifted_value

        # Not a valid type?
        else:
            out_type = out.device_type
            raise Exception(
                f"Invalid output type '{out_type}' for output with key '{key}'")

    def tick(self, mqtt):

        self._process_inputs()
        self._process_virtuals()
        self._process_outputs()
        self._shift_values()

    def _process_inputs(self):
        for key in self.inputs:
            # Do not call tick on pins dedicated to other functions (eg pins that are dedicated to SPI device)
            if key in self.dedicated_inputs:
                continue

            # Get input
            inp = self.inputs[key]

            # Process input
            topic = inp.tick(self._topic_host_name)

            # If topic returned, then publish topic
            if topic != None:
                self._mqtt.publish(topic, inp.value)

    def _process_outputs(self):
        self._output_controller.tick()

    def _process_virtuals(self):
        for key in self.virtuals:
            # Get virtual
            virt = self.virtuals[key]

            # Process virtual
            topic = virt.tick(self._topic_host_name)

            # If topic returned, then publish topic
            if topic != None:
                self._mqtt.publish(topic, virt.value)

    def _shift_values(self):
        # For each shift register, update its ouput (shift its values)
        for key in self._shift_registers:
            # Get the shift register instance
            shift_register = self._shift_registers[key]

            # Get the output values for the shift register
            outputs = bytes(shift_register.output_values)

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
            name = config.get_str("name", True, None)
            description = config.get_str("description", True, None)
            device_type = config.get_str("deviceType", True, "GPIO")
            pud = config.get_str("pud", True, "PUD_OFF")
            pin = config.get_int("pin", False, None, 0, 100)
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
            inp = Input(self, key, name, description, device_type,
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
            name = config.get_str("name", True, None)
            description = config.get_str("description", True, None)
            device_type = config.get_str("deviceType", True, "GPIO")
            pin = config.get_int("pin", False, None, 0, 100)
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
            out = Output(self, key, name, description, device_type, pin, topic,
                         interval, shift_register_key)

            # Add to output dictionary
            self.outputs[key] = out

            # If a GPIO pin then configure hardware
            if device_type == "GPIO":
                GPIO.setup(out.pin, GPIO.OUT)

    def __init_virtuals(self, virtuals):
        # Create virtuals definition dictionary
        self.virtuals = {}

        # Iterate virtual configurations
        for virtual_config in virtuals:
            config = DictionaryHelper(virtual_config, "virtual")

            # Get property values from config
            key = config.get_str("key", False, None)
            name = config.get_str("name", True, None)
            description = config.get_str("description", True, None)
            topic = config.get_str("topic", True, None)
            interval = config.get_int("interval", True, 3, 1, None)
            value = config.get_any("value", True, 0.0)

            # Can't add same key twice
            if key in self.virtuals:
                raise Exception("Virtual with key '{key}' already defined")

            # Create the definition
            virt = Virtual(self, key, name, description,
                           value, topic, interval)

            # Add to output dictionary
            self.virtuals[key] = virt

    def __init_shift_registers(self, shift_registers):
        # Create shift register instance dictionary
        self._shift_registers = {}

        # Iterate shift register configurations
        for shift_register_config in shift_registers:
            config = DictionaryHelper(shift_register_config, "shift register")

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

            # Add shift register pin keys to dedicated pin set
            self.dedicated_outputs[data] = True
            self.dedicated_outputs[clock] = True
            self.dedicated_outputs[data] = True
            self.dedicated_outputs[latch] = True

            if oe:
                self.dedicated_outputs[oe] = True

            if clear:
                self.dedicated_outputs[clear] = True

            # Create and add shift register
            shift_register = ShiftRegister(
                self, key, name, devices, outputs_per_device, data, clock, latch, oe, clear)

            self._shift_registers[key] = shift_register
