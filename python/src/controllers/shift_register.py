import RPi.GPIO as GPIO


class ShiftRegister:
    def __init__(self, io_manager, shift_register_def):
        self._devices = shift_register_def["devices"]
        self._data = io_manager.outputs[shift_register_def["data"]].pin
        self._clock = io_manager.outputs[shift_register_def["clock"]].pin
        self._latch = io_manager.outputs[shift_register_def["latch"]].pin
        
        self._oe = None
        if shift_register_def["oe"]:
            self._oe = io_manager.outputs[shift_register_def["oe"]].pin
        
        self._clear = None        
        if shift_register_def["clear"]:
            io_manager.outputs[shift_register_def["clear"]].pin

        self.__init_pins()

    def shift_clear_all(self):
        # If hardware clear pin defined, use a hardware clear
        if self._clear != None:
            GPIO.output(self._clear, 0)
            GPIO.output(self._clear, 1)
            return

        # hardware pin not defined, so do a software clear
        self.clear_latch()
        
        for i in range(self._devices):
            self.shift_byte(0)
        
        self.set_latch()

    def shift_bytes(self, bytes):
        for byte in bytes:
            self.shift_byte(byte)

    def shift_byte(self, byte):
        GPIO.output(self._clock, 0)

        for i in range(8):
            bit = (0x80 >> i) & byte
            self.__shift_bit(bit)

    def close(self):
        GPIO.cleanup()

    def enable_outputs(self):
        if self._oe != None:
            GPIO.output(self._oe, 0)  # Low enables outputs

    def disable_outputs(self):
        if self._oe != None:
            GPIO.output(self._oe, 1)  # High disables outputs

    def clear_latch(self):
        GPIO.output(self._latch, 0)

    def set_latch(self):
        GPIO.output(self._latch, 1)

    def __init_pins(self):
        # Clear current registers
        self.shift_clear_all()

        # Enable the outputs
        self.enable_outputs()

    def __shift_bit(self, bit):

        # Coerce to:
        #   0 for bit <= 0
        #   1 for bit >= 1
        if bit > 0:
            bit = 1
        else:
            bit = 0

        # Clock bit value
        GPIO.output(self._data, bit)
        GPIO.output(self._clock, 1)
        GPIO.output(self._clock, 0)
        return
