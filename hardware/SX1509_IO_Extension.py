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

# class SX1509:
#     def __init__(self, bus=1, address=SX1509_ADDRESS):
#         self.bus = SMBus(bus)
#         self.address = address
#         self.last_state = {}  # Store the last known state of each button
#         self.last_time = {}   # Store the last time a button state changed

#     def write_register(self, reg, value):
#         self.bus.write_byte_data(self.address, reg, value)

#     def read_register(self, reg):
#         return self.bus.read_byte_data(self.address, reg)

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
        if pin < 8:
            mask = 1 << pin
            dir_val = self.read_register(REG_DIR_A) | mask
            self.write_register(REG_DIR_A, dir_val)
            pull_val = self.read_register(REG_PULL_UP_A) | mask
            self.write_register(REG_PULL_UP_A, pull_val)
            in_val = self.read_register(REG_INPUT_DISABLE_A) & ~mask
            self.write_register(REG_INPUT_DISABLE_A, in_val)
        else:
            mask = 1 << (pin - 8)
            dir_val = self.read_register(REG_DIR_B) | mask
            self.write_register(REG_DIR_B, dir_val)
            pull_val = self.read_register(REG_PULL_UP_B) | mask
            self.write_register(REG_PULL_UP_B, pull_val)
            in_val = self.read_register(REG_INPUT_DISABLE_B) & ~mask
            self.write_register(REG_INPUT_DISABLE_B, in_val)

    def read_pin(self, pin):
        """
        Reads the raw state of a specific pin on the SX1509.

        Args:
            pin (int): The pin number to read (0-15).

        Returns:
            int: 0 if the button is pressed (low), 1 if not pressed (high).
        """
        if pin < 8:
            val = self.read_register(REG_DATA_A)
            return (val >> pin) & 0x01
        else:
            val = self.read_register(REG_DATA_B)
            return (val >> (pin - 8)) & 0x01

    def debounced_read_pin(self, pin):
        """Reads the pin state with debouncing to filter out spurious transitions.

        Args:
            pin (int): The pin number to read (0-15).

        Returns:
            int: 0 if the button is pressed (low), 1 if not pressed (high),
                after applying debouncing.
        """
        current_time = time.time()
        current_state = self.read_pin(pin)

        if pin not in self.last_state:
            # Initialize the last state and time for this pin
            self.last_state[pin] = current_state
            self.last_time[pin] = current_time
            return current_state

        if current_state != self.last_state[pin]:
            # State has changed, check if it's been stable for DEBOUNCE_TIME
            if current_time - self.last_time[pin] > DEBOUNCE_TIME:
                # State is stable, update last state and time
                self.last_state[pin] = current_state
                self.last_time[pin] = current_time
                return current_state
            else:
                # State is still bouncing, ignore it
                return self.last_state[pin]
        else:
            # State is the same as last time, update the last_time
            self.last_time[pin] = current_time
            return current_state

