
# # ! ---------------------------
# # ! Needs to run with sudo !!!!
# # ! ---------------------------

import time
import threading
import queue
from neopixel import NeoPixel
from board import D18
from colorama import Fore, Style

# GPIO-Pin für LEDs
LED_PIN = D18
NUM_PIXELS = 32
BRIGHTNESS = 0.5

# Farben definieren
COLORS = {
    "off": (0, 0, 0),
    "white": (255, 255, 255),
    "green": (12, 255, 28),
    "blue": (0, 0, 255),
    "yellow": (255, 255, 0),
    "orange-red": (255, 120, 0),
    "red": (255, 0, 0),
}

class LEDController:
    def __init__(self):
        self.strip = NeoPixel(LED_PIN, NUM_PIXELS, brightness=BRIGHTNESS, auto_write=False)
        self.led_queue = queue.Queue()
        self.stop_worker_event = threading.Event()
        self.stop_effect_event = threading.Event()
        self.worker_thread = None

    def start(self):
    #     if self.worker_thread is None or not self.worker_thread.is_alive():
        time.sleep(1) # Add a small delay
        """Starts the LED worker thread."""
        print(f"{Style.DIM}Starting LED worker{Style.RESET_ALL}")
        self.stop_worker_event.clear()
        self.worker_thread = threading.Thread(target=self._worker, daemon=True)
        self.worker_thread.start()
        time.sleep(0.1) # Add a small delay
    
    def stop(self):
        print(f"{Fore.RED}Stopping LED worker...{Style.RESET_ALL}")
        self.stop_worker_event.set()
        # Join the worker thread to ensure it's finished before exiting
        if self.worker_thread and self.worker_thread.is_alive():
            self.worker_thread.join(timeout=1)
        self.set_color("off")
        print(f"{Fore.RED}LED worker stopped.{Style.RESET_ALL}")

    def set_color(self, color):
        if color not in COLORS:
            print(f"{Fore.YELLOW}Invalid color requested for LED: {color}{Style.RESET_ALL}")
            return
        self.strip.fill(COLORS[color])
        self.strip.show()

    # led_controller.py (within the LEDController class)

    def set_effect(self, mode, color="white", **params):
        """Adds a new LED effect to the queue."""
        if mode not in ["static", "blink", "pulse", "fade"]:
            print(f"{Fore.YELLOW}Invalid mode requested for LED: {mode}{Style.RESET_ALL}")
            return
        
        print(f"{Style.DIM}Adding effect to queue: mode: {mode}, color: {color}, params: {params}{Style.RESET_ALL}")
        self.led_queue.put({"mode": mode, "color": color, "params": params})

    def _worker(self):
        print(f"{Style.DIM}LED worker thread started.{Style.RESET_ALL}")
        while not self.stop_worker_event.is_set():
            try:
                effect = self.led_queue.get(timeout=0.1)
                self.stop_effect_event.set()
                time.sleep(0.05)
                self.stop_effect_event.clear()

                mode = effect.get("mode")
                color = effect.get("color", "white")
                params = effect.get("params", {})
                
                self._run_effect(mode, color, params)
                
            except queue.Empty:
                continue
            except Exception as e:
                print(f"{Fore.RED}An error occurred in the LED worker: {e}{Style.RESET_ALL}")

    def _run_effect(self, mode, color, params):
        if mode == "static":
            self.set_color(color)
        elif mode == "blink":
            self._blink(color, **params)
        elif mode == "pulse":
            self._pulse(color, **params)

    def _blink(self, color, repeat=5, blink_interval=0.3):
        for _ in range(repeat):
            if self.stop_effect_event.is_set():
                self.set_color("off")
                return
            self.set_color(color)
            time.sleep(blink_interval)
            self.set_color("off")
            time.sleep(blink_interval)
        self.set_color("off")

    def _pulse(self, color, repeat=5, delay=0.03):
        if color not in COLORS:
            return
        
        start_rgb = COLORS["off"]
        end_rgb = COLORS[color]
        
        for _ in range(repeat):
            if self.stop_effect_event.is_set():
                self.set_color("off")
                return
            self._fade(start_rgb, end_rgb, steps=50, delay=delay)
            self._fade(end_rgb, start_rgb, steps=50, delay=delay)
        
        self.set_color("off")
        
    def _fade(self, start_color, end_color, steps, delay):
        for i in range(steps):
            if self.stop_effect_event.is_set():
                return
            
            factor = i / (steps - 1)
            r = int(start_color[0] + (end_color[0] - start_color[0]) * factor)
            g = int(start_color[1] + (end_color[1] - start_color[1]) * factor)
            b = int(start_color[2] + (end_color[2] - start_color[2]) * factor)
            
            self.strip.fill((r, g, b))
            self.strip.show()
            time.sleep(delay)

# Main for testing
if __name__ == "__main__":
    controller = LEDController()
    controller.start()
    print("Test sequence started.")
    try:
        controller.set_effect("static", "green")
        time.sleep(10)
        controller.set_effect("blink", "red", repeat=3, blink_interval=0.4)
        time.sleep(3)
        controller.set_effect("pulse", "blue", repeat=2, delay=0.02)
        time.sleep(5)
    except KeyboardInterrupt:
        print("Program interrupted.")
    finally:
        controller.stop()
        print("Test sequence finished.")