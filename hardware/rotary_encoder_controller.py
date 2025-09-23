import RPi.GPIO as GPIO
import time
import threading
from input_event import InputEvent 
import queue
from colorama import Fore, Style

class RotaryEncoderController:
    def __init__(self, name, event_queue, clk_pin, dt_pin, button_pin, options=None, steps_per_option=4):
        self.name = name
        self.event_queue = event_queue
        self.clk_pin = clk_pin
        self.dt_pin = dt_pin
        self.button_pin = button_pin

        self.options = options if options is not None else []
        self.current_index = 0
        self.steps_per_option = steps_per_option # New parameter to control sensitivity
        self.step_counter = 0 # New counter to track steps

        self.clk_last_state = 0
        self.thread = None
        self.running = False
        
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.clk_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.dt_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.button_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

        print(f"{Style.DIM}[{self.name}] RotaryEncoderController initialized with {len(self.options)} options.{Style.RESET_ALL}")
        
        self.clk_last_state = GPIO.input(self.clk_pin)

    def _poll_encoder(self):
        while self.running:
            # Check for button press
            button_state = GPIO.input(self.button_pin)
            if not button_state:
                event = InputEvent(self.name, self.options[self.current_index], {"name": self.name})
                self.event_queue.put(event)
                print(f"[{self.name}] Button pressed. Selected: {self.options[self.current_index]}")
                time.sleep(0.3)
            
            # Rotation logic
            clk_current_state = GPIO.input(self.clk_pin)
            if clk_current_state != self.clk_last_state:
                # A change has been detected on CLK. Now check DT.
                if GPIO.input(self.dt_pin) != clk_current_state:
                    self.step_counter += 1
                    direction = "clockwise"
                else:
                    self.step_counter -= 1
                    direction = "counter_clockwise"
                
                # Check if enough steps have passed to change the option
                if self.step_counter >= self.steps_per_option:
                    self.current_index = (self.current_index + 1) % len(self.options)
                    self.step_counter = 0  # Reset counter
                    event = InputEvent("encoder_rotation", self.options[self.current_index], {"name": self.name})
                    print(f"{Style.DIM}[{self.name}] Rotated: {direction}. {Style.DIM}{Style.NORMAL}New selection: {self.options[self.current_index]}{Style.RESET_ALL}")
                elif self.step_counter <= -self.steps_per_option:
                    self.current_index = (self.current_index - 1) % len(self.options)
                    self.step_counter = 0  # Reset counter
                    event = InputEvent("encoder_rotation", self.options[self.current_index], {"name": self.name})
                    print(f"{Style.DIM}[{self.name}] Rotated: {direction}. {Style.DIM}{Style.NORMAL}New selection: {self.options[self.current_index]}{Style.RESET_ALL}")
            
            self.clk_last_state = clk_current_state
            time.sleep(0.001)

    def start(self):
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._poll_encoder, daemon=True)
            self.thread.start()
            print(f"{Style.DIM}[{self.name}] Rotary encoder controller started.{Style.RESET_ALL}")

    def stop(self):
        if self.running:
            self.running = False
            if self.thread:
                self.thread.join()
            print(f"{Fore.RED}[{self.name}] Rotary encoder controller stopped.{Style.RESET_ALL}")

#  Test for main
if __name__ == "__main__":
    
    IMAGE_OPTIONS = [
    "chicken", "key", "book", "stick", "person", "ship", "bone", "phone", "dice", 
    "candle", "shoe", "door", "teeth", "knife", "apple", "sock", "car", "heart", 
    "potion", "dynamite"
    ]
    NUMBER_OPTIONS = [str(i) for i in range(1, 11)] # 10 numbers
    
    event_queue = queue.Queue()

    encoder = RotaryEncoderController(
        name="rotary_encoder",
        event_queue=event_queue,
        clk_pin=20,
        dt_pin=21,
        button_pin=16,
        options=NUMBER_OPTIONS,
        steps_per_option=4 # Adjust this value to change sensitivity
    )

    try:
        encoder.start()
        print("Rotate the knob or press the button to test. Ctrl+C to quit.\n")

        while True:
            try:
                event = event_queue.get(timeout=0.1)
                print(f"Event received: {event}")
            except queue.Empty:
                pass
    except KeyboardInterrupt:
        print("\nExiting...")
    finally:
        encoder.stop()
        GPIO.cleanup()