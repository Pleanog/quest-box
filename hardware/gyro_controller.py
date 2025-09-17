import smbus2
import time
import threading

# MPU-6050 Registers
MPU_ADDR = 0x68  # I2C address
PWR_MGMT_1 = 0x6B
ACCEL_XOUT_H = 0x3B
TEMP_OUT_H = 0x41
GYRO_XOUT_H = 0x43

# Constants for shake detection
SHAKE_THRESHOLD = 1.5  # Threshold for shake magnitude (adjust as needed)
SHAKE_TIME_THRESHOLD = 0.5  # Minimum time between shakes (in seconds)

class Gyro:
    def __init__(self, bus_id=1, address=MPU_ADDR, bus_lock=None):
        self.bus = smbus2.SMBus(bus_id)
        self.address = address
        self.bus_lock = bus_lock if bus_lock else threading.Lock()

        # Wake up the sensor
        with self.bus_lock:
            self.bus.write_byte_data(self.address, PWR_MGMT_1, 0)
        self.last_shake_time = time.time()

    def _read_word(self, reg):
        """Reads a 16-bit word from two consecutive registers."""
        with self.bus_lock:
            high = self.bus.read_byte_data(self.address, reg)
            low = self.bus.read_byte_data(self.address, reg + 1)
        value = (high << 8) + low
        return value - 65536 if value >= 0x8000 else value

    def read_sensor_data(self):
        # The lock is handled in _read_word, so no need to add another lock here.
        accel_x = self._read_word(ACCEL_XOUT_H) / 16384.0
        accel_y = self._read_word(ACCEL_XOUT_H + 2) / 16384.0
        accel_z = self._read_word(ACCEL_XOUT_H + 4) / 16384.0
        # We'll skip temperature and gyro data as we only need shake detection
        return accel_x, accel_y, accel_z
        
    def detect_shake(self, ax, ay, az):
        """Detect shake based on acceleration magnitude."""
        shake_magnitude = (ax**2 + ay**2 + az**2)**0.5
        current_time = time.time()
        
        if shake_magnitude > SHAKE_THRESHOLD and (current_time - self.last_shake_time) > SHAKE_TIME_THRESHOLD:
            self.last_shake_time = current_time
            return True
        return False

    def check_state(self):
        """
        Polls the gyro sensor and returns a dictionary of its current state.
        
        Returns:
            dict: A dictionary with keys 'shaking' and 'face_up'.
        """
        ax, ay, az = self.read_sensor_data()
        
        shaking = self.detect_shake(ax, ay, az)
        
        # You mentioned you are not interested in the 'face up' state,
        # but including the function for completeness if you change your mind.
        # It's better to return all possible states from a single check.
        face_up = 0 # Or you can add the logic back in here
        
        return {"shaking": shaking, "face_up": face_up}

# Example usage for testing
if __name__ == "__main__":
    gyro_sensor = Gyro()
    print("Gyro sensor initialized. Shake the device to test...")
    try:
        while True:
            state = gyro_sensor.check_state()
            if state["shaking"]:
                print("Shake detected! 💥")
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("Exiting...")