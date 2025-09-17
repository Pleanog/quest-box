import RPi.GPIO as GPIO
import time
import threading
from colorama import Fore, Style

# Constants
VIBRATION_PIN = 17

class VibrationController:
    """Controls a set of vibration motors connected to a single GPIO pin."""
    def __init__(self, pin=VIBRATION_PIN):
        self.pin = pin
        self.lock = threading.Lock()
        
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.pin, GPIO.OUT)
        GPIO.output(self.pin, GPIO.LOW)
        self.effect_thread = None
        self.stop_event = threading.Event()

    def _vibrate_effect(self, duration):
        """A simple, continuous vibration effect."""
        print(f"{Style.DIM}Starting vibration effect for {duration} seconds...{Style.RESET_ALL}")
        GPIO.output(self.pin, GPIO.HIGH)
        time.sleep(duration)
        GPIO.output(self.pin, GPIO.LOW)

    def _rattle_effect(self, duration, interval=0.1):
        """A rattling effect by pulsing the motors."""
        start_time = time.time()
        while time.time() - start_time < duration:
            GPIO.output(self.pin, GPIO.HIGH)
            time.sleep(interval)
            
            if self.stop_event.is_set():
                break
                
            GPIO.output(self.pin, GPIO.LOW)
            time.sleep(interval)
        
        GPIO.output(self.pin, GPIO.LOW)

    def stop(self):
        """Signals the currently running effect to stop."""
        print(f"{Fore.RED}Stopping Vibration Worker ...{Style.RESET_ALL}")
        self.stop_event.set()
        GPIO.output(self.pin, GPIO.LOW)
        self.cleanup()

    def set_effect(self, mode: str, duration: float, **params):
        """
        Sets a new vibration effect.
        """
        # Ensure only one thread runs at a time
        with self.lock:
            # Check if an old thread is still running
            if self.effect_thread and self.effect_thread.is_alive():
                self.stop()
                self.effect_thread.join(timeout=1)
                self.stop_event.clear()

            # Select the new effect function
            if mode == "vibrate":
                target_func = self._vibrate_effect
            elif mode == "rattle":
                target_func = self._rattle_effect
            else:
                print(f"Warning: Unknown vibration mode '{mode}'")
                return

            # Start the new effect thread
            self.effect_thread = threading.Thread(
                target=target_func,
                args=(duration,),
                kwargs=params,
                daemon=True
            )
            self.effect_thread.start()
            
    def cleanup(self):
        """Stops any running effect and cleans up GPIO."""
        self.stop_event.set()
        if self.effect_thread and self.effect_thread.is_alive():
            self.effect_thread.join(timeout=1)
        
        GPIO.cleanup(self.pin)
        print("Vibration controller cleaned up.")


if __name__ == "__main__":

    controller = VibrationController()

    try:
        print("Testing vibrate effect for 2 seconds...")
        controller.set_effect("vibrate", 2)
        time.sleep(2.5)

        print("Testing rattle effect for 3 seconds...")
        controller.set_effect("rattle", 3, interval=0.2)
        time.sleep(3.5)

        print("Testing stop during rattle effect...")
        controller.set_effect("rattle", 5, interval=0.1)
        time.sleep(2)
        controller.stop()

    except KeyboardInterrupt:
        print("Interrupted by user.")
    finally:
        controller.cleanup()