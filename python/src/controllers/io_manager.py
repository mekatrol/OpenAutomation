import RPi.GPIO as GPIO
from controllers.shift_register import ShiftRegister


class IoManager:
    def __init__(self, config):
        # If no IO section then don't process further
        if not "io" in config:
            return

        # Get IO config
        io_conf = config["io"]

        # Get GPIO pin numbering mode
        if not "pinNumberingMode" in io_conf:
            # Need pin numbering mode to be able to use IO
            raise Exception("The pin numbering mode has not been defined (using the 'pinNumberingMode' property (valid values: 'BCM', 'BOARD')")
        pin_numbering_mode = io_conf["pinNumberingMode"]

        # Set GPIO pin numbering mode
        if pin_numbering_mode == "BCM":
            GPIO.setmode(GPIO.BCM)
        elif pin_numbering_mode == "BOARD":
            GPIO.setmode(GPIO.BOARD)
        else:
            raise Exception("pinNumberingMode value must be set to 'BCM' or 'BOARD'")

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

    def input(self, key):
        # To read an input then the input config must exist
        if not key in self.inputs:
            raise Exception(f"Invalid input key '{key}'")

        # Use GPIO to return value based in input config
        return GPIO.input(self.inputs[key]["pin"])

    def output(self, key, value):
        # To write an ouput then the output config must exist
        if not key in self.outputs:
            raise Exception(f"Invalid output key '{key}'")

        # Get the output config
        out = self.outputs[key]

        # If the output is a GPIO type then set output value using
        # GPIO library
        if out["type"] == "GPIO":
            GPIO.output(out["pin"], value)

        # If the output is a shift register output for a shift register then
        # update shift register output value
        elif out["type"] == "SR":
            # Get the referenced shift register
            shift_register_def = self._shift_register_defs[out["shift_register_key"]]

            # Get the number of output bits per device
            outputs_per_device = shift_register_def["outputs_per_device"]

            # Get the shift register pin number, this is the output number
            # from 1 to n where n is the max number of outputs for the 
            # total number of devices.
            # For example, if there are two 74HC595 devices chained then
            # the total number of outputs will be 16 (2 devices x 8 outputs each device)
            shift_register_pin = out["pin"]

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
            out_type = out["type"]
            raise Exception(
                f"Invalid output type '{out_type}' for output with key '{key}'")

    def shift_values(self):
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
            if not "key" in input_config:
                raise Exception(
                    "'key' property must be defined for all inputs")

            if not "pin" in input_config:
                raise Exception(
                    "'pin' property must be defined for all inputs")

            if not "pud" in input_config:
                raise Exception(
                    "'pud' property must be defined for all inputs")

            # Get property default values
            key = input_config["key"]
            pin = input_config["pin"]
            pud = GPIO.PUD_OFF
            name = None
            topic = None
            interval = 1

            # If optional name defined then get value
            if "name" in input_config:
                name = input_config["name"]

            # If optional topic defined then get value
            if "topic" in input_config:
                topic = input_config["topic"]

            # If optional interval defined then get value
            if "interval" in input_config:
                interval = input_config["interval"]

            # Convert pull_up_down definition
            if input_config["pud"] == "PUD_UP":
                pud = GPIO.PUD_UP

            elif input_config["pud"] == "PUD_DOWN":
                pud = GPIO.PUD_DOWN

            elif input_config["pud"] != "PUD_OFF":
                raise Exception("Input invalid 'pud' property value")

            # Key must be a valid string and must not be empty
            if not key or type(key) != str:
                raise Exception(
                    "Input 'key' property must be a valid string value")

            # Pin must be an integer and >= zero
            if not pin or pin < 0 or not isinstance(pin, int):
                raise Exception(
                    "Input 'pin' property must be a valid integer value >= 0")

            # Can't add same key twice
            if key in self.inputs:
                raise Exception("Input with key '{key}' already defined")

            inp = {
                "key": key,
                "name": name,
                "pin": pin,
                "pud": pud,
                "topic": topic,
                "interval": interval
            }

            self.inputs[key] = inp

            GPIO.setup(inp["pin"], GPIO.IN, pull_up_down=pud)

    def __init_outputs(self, outputs):
        # Create output definition dictionary
        self.outputs = {}

        # Iterate output configurations
        for output_config in outputs:
            if not "key" in output_config:
                raise Exception(
                    "'key' property must be defined for all outputs")

            if not "pin" in output_config:
                raise Exception(
                    "'pin' property must be defined for all outputs")

            if not "type" in output_config:
                raise Exception(
                    "'type' property must be defined for all outputs")

            # Get property default values
            key = output_config["key"]
            pin_type = output_config["type"]
            pin = output_config["pin"]
            name = None
            topic = None
            interval = 1
            shift_register_key = None

            # Validate type
            if pin_type != "GPIO" and pin_type != "SR":
                raise Exception("Output invalid 'type' property value")

            # If optional name defined then get value
            if "name" in output_config:
                name = output_config["name"]

            # If optional topic defined then get value
            if "topic" in output_config:
                topic = output_config["topic"]

            # If optional interval defined then get value
            if "interval" in output_config:
                interval = output_config["interval"]

            # If optional shift register key defined then get value
            if pin_type == "SR":
                if not "shiftRegisterKey" in output_config:
                    raise Exception(
                        f"shiftRegisterkey property must be defined for output with key '{key}'")
                shift_register_key = output_config["shiftRegisterKey"]

            # Key must be a valid string and must not be empty
            if not key or type(key) != str:
                raise Exception(
                    "Output 'key' property must be a valid string value")

            # Pin must be an integer and >= zero
            if not pin or pin < 0 or not isinstance(pin, int):
                raise Exception(
                    "Output 'pin' property must be a valid integer value >= 0")

            # Can't add same key twice
            if key in self.outputs:
                raise Exception("Output with key '{key}' already defined")

            out = {
                "key": key,
                "name": name,
                "type": pin_type,
                "pin": pin,
                "topic": topic,
                "interval": interval,
                "shift_register_key": shift_register_key
            }

            self.outputs[key] = out

            if out["type"] == "GPIO":
                GPIO.setup(out["pin"], GPIO.OUT)

    def __init_shift_registers(self, shift_registers):
        # Create shift register definition dictionary
        self._shift_register_defs = {}

        # Create shift register instance dictionary
        self._shift_registers = {}

        # Iterate shift register configurations
        for shift_register_config in shift_registers:
            if not "key" in shift_register_config:
                raise Exception(
                    "'key' property must be defined for all shift registers")

            if not "data" in shift_register_config:
                raise Exception(
                    "'data' property must be defined for all shift registers")

            if not "clock" in shift_register_config:
                raise Exception(
                    "'clock' property must be defined for all shift registers")

            if not "latch" in shift_register_config:
                raise Exception(
                    "'latch' property must be defined for all shift registers")

            if not "devices" in shift_register_config:
                raise Exception(
                    "'devices' property must be defined for all shift registers")

            oe = None
            clear = None

            key = shift_register_config["key"]
            devices = shift_register_config["devices"]
            outputs_per_device = 8 # Default to 8 output pins per device 
            data = shift_register_config["data"]
            clock = shift_register_config["clock"]
            latch = shift_register_config["latch"]

            if not data in self.outputs:
                raise Exception(
                    f"Data output name '{data}' not a valid output name")

            if not clock in self.outputs:
                raise Exception(
                    f"Clock output name '{clock}' not a valid output name")

            if not latch in self.outputs:
                raise Exception(
                    f"Latch output name '{latch}' not a valid output name")

            if "oe" in shift_register_config:
                oe = shift_register_config["oe"]
                if oe != None and not oe in self.outputs:
                    raise Exception(
                        f"Output enable output name '{oe}' not a valid output name")

            if "clear" in shift_register_config:
                clear = shift_register_config["clear"]
                if clear != None and not clear in self.outputs:
                    raise Exception(
                        f"Clear output name '{clear}' not a valid output name")

            # If optional outputs per device defined then get value
            if "outputsPerDevice" in shift_register_config:
                outputs_per_device = shift_register_config["outputsPerDevice"]

            # If optional name defined then get value
            if "name" in shift_register_config:
                name = shift_register_config["name"]

            # Create array to hold 8 bit values for each device
            output_values =[0] * devices

            # Can't add same key twice
            if key in self._shift_register_defs:
                raise Exception(
                    "Shift register with key '{key}' already defined")

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
                "outputs_per_device": outputs_per_device
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
