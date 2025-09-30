import queue
import time
from threading import Thread, Lock
import RPi.GPIO as GPIO
from colorama import Fore, Style

# Helper Class
from input_event import InputEvent 

# Controllers
from SX1509_IO_Extension import SX1509
from gyro_controller import Gyro
from rotary_encoder_controller import RotaryEncoderController 
from distance_controller import DistanceController

IMAGE_OPTIONS = ["dynamite", "knife", "candle", "rope", "key", "book", "dice", "potion", "stick", "compass"] # 10 images
NUMBER_OPTIONS = [str(i) for i in range(0, 10)] # 10 numbers

class InputManager:
    def __init__(self, event_queue, bus_lock, device_configs):
        self.event_queue = event_queue
        self.bus_lock = bus_lock
        self.running = False
        self.worker_thread = None
        self.controllers = {}
        
        # Initialize the I2C controllers with the shared bus_lock
        self.sx1509 = SX1509(bus_lock=self.bus_lock)
        self.gyro_sensor = Gyro(bus_lock=self.bus_lock)
        
        self.polling_functions = []
        
        self.handlers = {
            "sx1509_button": self._handle_sx1509_button,
            "gyro": self._handle_gyro,
            "rotary_encoder": self._handle_rotary_encoder,
            "distance_sensor": self._handle_distance_sensor,
        }

        for config in device_configs:
            self.add_device(config)

    def _handle_sx1509_button(self, config):
        color = config["value"]
        pin = config["pin"]
        self.sx1509.setup_input_with_pullup(pin)
        self.polling_functions.append(self._create_button_checker(color, pin))
        print(f"{Style.DIM}Configured SX1509 button '{color}' on IO{pin}{Style.RESET_ALL}")

    def _create_button_checker(self, color, pin):
        def check_button():
            state = self.sx1509.debounced_read_pin(pin)
            if state == 0:
                event = InputEvent("button", color)
                self.event_queue.put(event)
                print(f"{Style.DIM}SX1509 Button {color} pressed.{Style.RESET_ALL}")
        return check_button
    
    def _handle_gyro(self, config):
        self.polling_functions.append(self._create_gyro_checker())
        print(f"{Style.DIM}Configured gyro{Style.RESET_ALL}")

    def _create_gyro_checker(self):
        def check_gyro():
            try:
                state = self.gyro_sensor.check_state()
                if state["shaking"]:
                    event = InputEvent("gyro", "shaking", {"details": state})
                    self.event_queue.put(event)
                    print("Gyro shaking detected.")
            except OSError as e:
                print(f"I2C Error during gyro check: {e}")
        return check_gyro

    def _handle_rotary_encoder(self, config):
        name = config["name"]
        clk_pin = config["clk_pin"]
        dt_pin = config["dt_pin"]
        button_pin = config["button_pin"]
        
        options = []
        if name == "rotary_encoder_picture":
            options = IMAGE_OPTIONS
        elif name == "rotary_encoder_number":
            options = NUMBER_OPTIONS
        
        encoder_controller = RotaryEncoderController(
            name=name,
            event_queue=self.event_queue,
            clk_pin=clk_pin,
            dt_pin=dt_pin,
            button_pin=button_pin,
            options=options
        )
        self.controllers[name] = encoder_controller
        print(f"{Style.DIM}Configured rotary encoder '{name}' with {len(options)} options.{Style.RESET_ALL}")

    def _handle_distance_sensor(self, config):
        name = config.get("name", "distance_sensor")
        trigger_pin = config["trigger_pin"]
        echo_pin = config["echo_pin"]
        
        distance_controller = DistanceController(
            name=name,
            event_queue=self.event_queue,
            trigger_pin=trigger_pin,
            echo_pin=echo_pin
        )
        self.controllers[name] = distance_controller
        print(f"{Style.DIM}Configured distance sensor '{name}' on pins TRIG={trigger_pin}, ECHO={echo_pin}{Style.RESET_ALL}")
        

    def add_device(self, config):
        device_type = config.get("type")
        if device_type in self.handlers:
            self.handlers[device_type](config)
        else:
            print(f"Warning: Unsupported device type '{device_type}'")

    def start(self):
        self.running = True
        print("InputManager started.")
        self.worker_thread = Thread(target=self.poll_devices, daemon=True)
        self.worker_thread.start()
        
        for controller in self.controllers.values():
            if hasattr(controller, 'start'):
                controller.start()

    def stop(self):
        self.running = False
        if self.worker_thread and self.worker_thread.is_alive():
            self.worker_thread.join()
            
        for controller in self.controllers.values():
            if hasattr(controller, 'stop'):
                controller.stop()

        print("InputManager stopped.")

    def poll_devices(self):
        while self.running:
            for check_func in self.polling_functions:
                check_func()
                time.sleep(0.05) 

# Example usage for testing
if __name__ == "__main__":
    q = queue.Queue()
    bus_lock = Lock()

    device_configs = [
        
        {"type": "sx1509_button", "value": "repeat", "pin": 11},
        {"type": "sx1509_button", "value": "hint", "pin": 3},
        {"type": "sx1509_button", "value": "yellow", "pin": 4},
        {"type": "sx1509_button", "value": "red", "pin": 1},
        {"type": "sx1509_button", "value": "green", "pin": 14},
        {"type": "sx1509_button", "value": "blue", "pin": 13},
        {"type": "gyro", "value": "shaking"},
        {"type": "rotary_encoder", "name": "rotary_encoder_picture", "clk_pin": 20, "dt_pin": 21, "button_pin": 16},
        {"type": "rotary_encoder", "name": "rotary_encoder_number", "clk_pin": 13, "dt_pin": 19, "button_pin": 26},
        {"type": "distance_sensor", "trigger_pin": 23, "echo_pin": 24},
    ]

    im = InputManager(q, bus_lock, device_configs)
    
    im.start()
    print("Listening for input events. Press Ctrl+C to exit.")
    try:
        while True:
            if not q.empty():
                event = q.get()
                print(f"Main loop received: {event}")
            time.sleep(1)
    except KeyboardInterrupt:
        print("Exiting...")
    finally:
        im.stop()