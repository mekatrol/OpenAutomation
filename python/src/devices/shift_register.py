import RPi.GPIO as GPIO


class ShiftRegister:
    def __init__(self, io_manager,
                 key, name, devices, outputs_per_device,
                 data, clock, latch, oe, clear):

        self.key = key
        self.name = name

        self._io_manager = io_manager
        self._devices = devices
        self.outputs_per_device = outputs_per_device
        self._data = data
        self._clock = clock
        self._latch = latch
        self._oe = oe
        self._clear = clear

        self._data_pin = io_manager.outputs[data].pin
        self._clock_pin = io_manager.outputs[clock].pin
        self._latch_pin = io_manager.outputs[latch].pin

        self._oe_pin = None
        if oe in io_manager.outputs:
            self._oe_pin = io_manager.outputs[oe].pin

        self._clear_pin = None
        if clear in io_manager.outputs:
            self._clear_pin = io_manager.outputs[clear].pin

        # Create array to hold 8 bit values for each device
        self.output_values = [0] * devices

    def shift_and_latch(self, byte_values):
        # Clear latch
        self.clear_latch()

        # Send output values to clear bits
        self.shift_bytes(byte_values)

        # Latch values
        self.set_latch()

    def shift_bytes(self, byte_values):
        # Reverse array order so that the last device is shifted first
        reversed_byte_values = reversed(byte_values)

        for byte in reversed_byte_values:
            self.shift_byte(byte)

    def shift_byte(self, byte):
        GPIO.output(self._clock_pin, 0)

        for i in range(8):
            bit = (0x80 >> i) & byte
            self.__shift_bit(bit)

    def close(self):
        GPIO.cleanup()

    def enable_outputs(self):
        if self._oe_pin != None:
            GPIO.output(self._oe_pin, 0)  # Low enables outputs

    def disable_outputs(self):
        if self._oe_pin != None:
            GPIO.output(self._oe_pin, 1)  # High disables outputs

    def clear_latch(self):
        GPIO.output(self._latch_pin, 0)

    def set_latch(self):
        GPIO.output(self._latch_pin, 1)

    def __shift_bit(self, bit):

        # Coerce to:
        #   0 for bit <= 0
        #   1 for bit >= 1
        if bit > 0:
            bit = 1
        else:
            bit = 0

        # Clock bit value
        GPIO.output(self._data_pin, bit)
        GPIO.output(self._clock_pin, 1)
        GPIO.output(self._clock_pin, 0)
        return
