import RPi.GPIO as GPIO
from controllers.shift_register import ShiftRegister


class IoManager:
    def __init__(self, config):
        # If no IO section then don't process further
        if not "io" in config:
            return

        # Get io config
        io_conf = config["io"]

        # Get GPIO mode
        if not "mode" in io_conf:
            # Need IO mode to be able to use IO
            raise Exception("The IO mode has not been defined")

        io_mode = io_conf["mode"]

        if io_mode == "BCM":
            GPIO.setmode(GPIO.BCM)
        elif io_mode == "BOARD":
            GPIO.setmode(GPIO.BOARD)
        else:
            raise Exception("Mode value must be set to 'BCM' or 'BOARD'")

        # Dedicated IO pins are those GPIO pins that a dedicated to 
        # another purpose (eg shift register control pin). The should not
        # be controllable as a general IO pin
        self.dedicated_inputs = {}
        self.dedicated_outputs = {}

        # Are there inputs defined?
        if "inputs" in io_conf:
            self.__init_inputs(io_conf["inputs"])

        # Are there outputs defined?
        if "outputs" in io_conf:
            self.__init_outputs(io_conf["outputs"])

        # Are there shift registers defined?
        if "shiftRegisters" in io_conf:
            self.__init_shift_registers(io_conf["shiftRegisters"])

    def input(self, key):
        if not key in self.inputs:
            raise Exception(f"Invalid input key '{key}'")

        return GPIO.input(self.inputs[key]["pin"])

    def output(self, key, value):
        if not key in self.outputs:
            raise Exception(f"Invalid output key '{key}'")

        out = self.outputs[key]

        if out["type"] == "GPIO":
            GPIO.output(out["pin"], value)

        elif out["type"] == "SR":
            shift_register_def = self._shift_register_defs[out["shift_register_key"]]

            pin = out["pin"]

            # Get the device number that the pin belongs to
            device = int(pin / 8)

            # Get the pin number on the device (modulo 8 as a bits per device)
            pin = pin % 8

            pin_shifted_value = 1 << (pin - 1)

            if value == 1:
                shift_register_def["output_values"][device] |= pin_shifted_value
            else:
                shift_register_def["output_values"][device] &= ~pin_shifted_value

        else:
            out_type = out["type"]
            raise Exception(
                f"Invalid output type '{out_type}' for output with key '{key}'")

    def shift_values(self):
        for key in self._shift_register_defs:
            shift_register_def = self._shift_register_defs[key]
            shift_register = self._shift_registers[key]

            outputs = bytes(shift_register_def["output_values"])

            #shift_bytes = outputs.to_bytes(shift_register_def["devices"], 'big')

            # Shift bit values to output shift register
            shift_register.clear_latch()
            shift_register.shift_bytes(outputs)
            shift_register.set_latch()

    def __init_inputs(self, inputs):
        self.inputs = {}

        # Setup inputs
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
        self.outputs = {}

        # Setup outputs
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
        self._shift_register_defs = {}
        self._shift_registers = {}

        # Setup shift registers
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
