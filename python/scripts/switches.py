class ScriptModule:
    def init(self, key, init_data, inputs, outputs, virtuals):
        self.key = key
        if init_data == None:
            raise Exception(
                f"Script module with key '{key}' missing required initialisation init data")

        if not "input" in init_data:
            raise Exception(
                f"Script module with key '{key}' missing required init data 'input' value")

        if not "output" in init_data:
            raise Exception(
                f"Script module with key '{key}' missing required inr data 'output' value")

        self.input_name = init_data["input"]
        self.output_name = init_data["output"]

        # Get the switch initial value
        self.sw_value_last_tick = inputs[self.input_name].value

    def tick(self, data):
        # Get the switch value
        sw_value = data.inputs[self.input_name].value

        # Get the current output value
        op_value = data.outputs[self.output_name].value

        # Set output if switch is on
        if sw_value == 1 and sw_value != self.sw_value_last_tick:
            # Toggle output value
            if op_value > 0:
                data.outputs[self.output_name].value = 0
            else:
                data.outputs[self.output_name].value = 1

        # Remember switch value for next tick
        self.sw_value_last_tick = sw_value

        # Returning false will cancel further modules from being processed
        return True
