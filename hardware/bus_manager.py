import threading
from SX1509_IO_Extension import SX1509
from gyro_controller import Gyro

# Creates a single, shared I2C bus lock
I2C_BUS_LOCK = threading.Lock()