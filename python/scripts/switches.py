class ScriptModule:
    def init(self, key, data):
        self.key = key
        if data == None:
            raise Exception(
                f"Script module with key '{key}' missing required initialisation data")

        if not "input" in data:
            raise Exception(
                f"Script module with key '{key}' missing required data 'input' value")

        if not "output" in data:
            raise Exception(
                f"Script module with key '{key}' missing required data 'output' value")

        self.input_name = data["input"]
        self.output_name = data["output"]
        self.sw_value_last_tick = 0

    def tick(self, data):
        # Get the switch value
        sw_value = data.inputs[self.input_name].value

        # Set output if switch is on
        if sw_value and sw_value != self.sw_value_last_tick:
            data.outputs[self.output_name].value = 1

        # Remember value for next tick
        self.sw_value_last_tick = sw_value
