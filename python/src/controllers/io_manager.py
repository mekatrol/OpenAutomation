import RPi.GPIO as GPIO


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

        return GPIO.output(self.outputs[key]["pin"], value)

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

            # Validate type
            if pin_type != "GPIO" and pin_type != "SR":
                raise Exception("Output invalid 'type' property value")

            # If optional name defined then get value
            if "name" in output_config:
                name = output_config["name"]

            # If optional topic defined then get value
            if "topic" in output_config:
                topic = output_config["topic"]

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
                "topc": topic
            }

            self.outputs[key] = out

            if out["type"] == "GPIO":
                GPIO.setup(out["pin"], GPIO.OUT)

    def __init_shift_registers(self, shift_registers):
        self.shift_registers = {}

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

            # Can't add same key twice
            if key in self.shift_registers:
                raise Exception(
                    "Shift register with key '{key}' already defined")

            shift_register = {
                "key": key,
                "name": name,
                "devices": devices,
                "data": data,
                "clock": clock,
                "latch": latch,
                "oe": oe,
                "clear": clear
            }

            self.shift_registers[key] = shift_register
