from smbus2 import SMBus
import time
import threading

SX1509_ADDRESS = 0x3E

# SX1509 registers
REG_INPUT_DISABLE_B = 0x00
REG_INPUT_DISABLE_A = 0x01
REG_PULL_UP_B       = 0x06
REG_PULL_UP_A       = 0x07
REG_DIR_B           = 0x0E
REG_DIR_A           = 0x0F
REG_DATA_B          = 0x10
REG_DATA_A          = 0x11

DEBOUNCE_TIME = 0.1  # Debounce time in seconds

class SX1509:
    def __init__(self, bus=1, address=SX1509_ADDRESS, bus_lock=None):
        self.bus = SMBus(bus)
        self.address = address
        self.bus_lock = bus_lock if bus_lock else threading.Lock()
        self.last_state = {}
        self.last_time = {}

    def write_register(self, reg, value):
        with self.bus_lock:
            self.bus.write_byte_data(self.address, reg, value)

    def read_register(self, reg):
        with self.bus_lock:
            return self.bus.read_byte_data(self.address, reg)

    def setup_input_with_pullup(self, pin):
        """Sets up a pin as an input with an internal pull-up resistor."""
        # Determine the correct registers and mask based on the pin number
        if pin < 8:
            mask = 1 << pin
            reg_dir, reg_pull, reg_in = REG_DIR_A, REG_PULL_UP_A, REG_INPUT_DISABLE_A
        else:
            mask = 1 << (pin - 8)
            reg_dir, reg_pull, reg_in = REG_DIR_B, REG_PULL_UP_B, REG_INPUT_DISABLE_B

        # Now, execute the logic once with the correct variables
        dir_val = self.read_register(reg_dir) | mask
        self.write_register(reg_dir, dir_val)

        pull_val = self.read_register(reg_pull) | mask
        self.write_register(reg_pull, pull_val)

        in_val = self.read_register(reg_in) & ~mask
        self.write_register(reg_in, in_val)

    def read_pin(self, pin):
        """
        Reads the raw state of a specific pin.
        Returns: 0 if pressed (low), 1 if not pressed (high).
        """
        # Determine the correct register and bit shift based on the pin number
        if pin < 8:
            reg_data = REG_DATA_A
            shift = pin
        else:
            reg_data = REG_DATA_B
            shift = pin - 8
        
        # Read the register and extract the specific pin's state
        val = self.read_register(reg_data)
        return (val >> shift) & 0x01

    def debounced_read_pin(self, pin):
        """
        Reads the pin state with debouncing to filter out spurious transitions.
        Returns: 0 if pressed (low), 1 if not pressed (high).
        """
        current_time = time.time()
        current_state = self.read_pin(pin)

        if pin not in self.last_state:
            # Initialize the last state and time for this pin
            self.last_state[pin] = current_state
            self.last_time[pin] = current_time
            return current_state

        last_known_state = self.last_state[pin]
        if current_state != last_known_state:
            # State has changed, reset the timer
            self.last_time[pin] = current_time
            self.last_state[pin] = current_state
            return last_known_state  # Return previous stable state during bounce
        
        # State is stable, check if debounce time has passed
        if current_time - self.last_time[pin] > DEBOUNCE_TIME:
            return current_state  # Return the new stable state
        else:
            return last_known_state # Not stable long enough, return old state