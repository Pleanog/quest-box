import RPi.GPIO as GPIO
import time
import threading
import queue
from input_event import InputEvent
from colorama import Fore, Style

class DistanceController:
    def __init__(self, name, event_queue, trigger_pin, echo_pin):
        self.name = name
        self.event_queue = event_queue
        self.trigger_pin = trigger_pin
        self.echo_pin = echo_pin
        self.last_state = None
        self.running = False
        self.thread = None

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.trigger_pin, GPIO.OUT)
        GPIO.setup(self.echo_pin, GPIO.IN)
        GPIO.output(self.trigger_pin, False)

    def _get_distance(self):
        """Measures the distance from the sensor."""
        GPIO.output(self.trigger_pin, True)
        time.sleep(0.00001)
        GPIO.output(self.trigger_pin, False)

        start_time = time.time()
        stop_time = time.time()

        while GPIO.input(self.echo_pin) == 0:
            start_time = time.time()
        while GPIO.input(self.echo_pin) == 1:
            stop_time = time.time()

        time_elapsed = stop_time - start_time
        distance = (time_elapsed * 34300) / 2
        return distance

    def _get_state(self):
        """Returns 'covered', 'hovered', or 'clear' based on distance."""
        distance = self._get_distance()
        if distance < 6:
            return "covered"
        elif 6 <= distance < 60:
            return "hovered"
        else:
            return "clear"

    def _poll_sensor(self):
        """Worker function to periodically check the sensor state."""
        while self.running:
            current_state = self._get_state()
            if current_state != self.last_state:
                event = InputEvent("distance_sensor", current_state)
                if self.last_state is not None:
                    self.event_queue.put(event)
                    print(f"{Style.DIM}[{self.name}] State change: {self.last_state} -> {current_state}{Style.RESET_ALL}")
                self.last_state = current_state
            
            time.sleep(2) # Poll every 2 seconds

    def start(self):
        """Starts the sensor polling thread."""
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._poll_sensor, daemon=True)
            self.thread.start()
            print(f"{Style.DIM}[{self.name}] Distance sensor controller started.{Style.RESET_ALL}")

    def stop(self):
        """Stops the sensor polling thread."""
        if self.running:
            self.running = False
            if self.thread:
                self.thread.join()
            print(f"[{self.name}] Distance sensor controller stopped.")



#  Test for main
if __name__ == "__main__":
    event_queue = queue.Queue()
    controller = DistanceController(
        name="MyDistanceSensor",
        event_queue=event_queue,
        trigger_pin=23,
        echo_pin=24,
    )
    print(f"[{controller.name}] Distance sensor controller created.")
    try:
        controller.start()
        while True:
            try:
                event = event_queue.get(timeout=1)  # wait max 1s for an event
                print(f"Event received: {event.value}")
            except queue.Empty:
                pass  
    except KeyboardInterrupt:
        print("Stopping...")
    finally:
        controller.stop()
        GPIO.cleanup()
