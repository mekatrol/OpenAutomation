class ScriptModule:
    def init(self, key, init_data, inputs, outputs, virtuals, onewires):
        self.key = key
        if init_data == None:
            raise Exception(
                f"Script module with key '{key}' missing required initialisation init data")

        if not "onewire" in init_data:
            raise Exception(
                f"Script module with key '{key}' missing required init data 'onewire' value")

        if not "output" in init_data:
            raise Exception(
                f"Script module with key '{key}' missing required inr data 'output' value")

        self.onewire_name = init_data["onewire"]
        self.output_name = init_data["output"]

    def tick(self, data):
        # Get the switch value
        temperature_1 = data.onewires["temperature_1"].value
        temperature_2 = data.onewires["temperature_2"].value

        temperature = (temperature_1 + temperature_2) / 2

        # Get the setpoint
        setpoint = data.virtuals["heater_setpoint"].value
        pb = data.virtuals["heater_pb"].value

        # Set output if switch is on
        if temperature <= setpoint:
            data.outputs[self.output_name].value = 1
        elif temperature > setpoint + pb:
            data.outputs[self.output_name].value = 0

        # Returning false will cancel further modules from being processed
        return True
