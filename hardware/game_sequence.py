import json
import time
import threading
import queue
import copy
from pathlib import Path
from input_manager import InputEvent
from output_manager import OutputManager
from colorama import Fore, Style

#  ---- Registry --------
SENSOR_REGISTRY = {
    "button": {
        "required": ["value"],
        "aliases": {"count": "times", "presses": "times", "num": "times"},
    },
    "joystick": {
        "required": ["value"],
        "aliases": {},
    },
    # "color_sensor": {
    #     "required": ["value"],
    #     "aliases": {"color": "colour"},
    # },
    "distance_sensor": {
        "required": ["value"], # The states (covered, hovered, clear)
        "aliases": {},
    },
    "gyro": {
        "required": ["value"],
        "aliases": {},
    },
    "rotary_encoder_number": {
        "required": ["value"], # This is a dictionary of 10 values
        "aliases": {},
    },
    "rotary_encoder_picture": {
        "required": ["value"], # This is a dictionary of 10 values
        "aliases": {},
    }
}

# -------- Error handlers --------
def handle_game_over():
    print("💥 Game Over!")
    
def handle_timeout():
    print("⏰ Time's up!")
    handle_game_over()
    
ERROR_HANDLERS = {
    "game_over": handle_game_over,
}

# -------- Utilities --------
def _normalize_and_validate_step(step: dict) -> tuple[str, dict]:
    """
    Returns (component_type, params) after:
      - verifying component exists
      - applying alias mappings
      - checking required fields
    """
    if "sensor" in step:
        component_type_key = "sensor"
        registry = SENSOR_REGISTRY
    elif "actuator" in step:
        component_type_key = "actuator"
        # For actuators, we don't need a registry to validate parameters
        # because the OutputManager now handles this.
        registry = {}
    else:
        raise ValueError("Step is missing 'sensor' or 'actuator'.")
    
    component_type = step[component_type_key]
    
    # Validation logic specific to sensors
    if component_type_key == "sensor":
        if component_type not in registry:
            raise ValueError(f"Unknown sensor component '{component_type}'.")
        
        spec = registry[component_type]
        aliases = spec.get("aliases", {})
        required = spec.get("required", [])

        params_raw = { (aliases.get(k, k)): v for k, v in step.items() if k != component_type_key }

        missing = [k for k in required if k not in params_raw]
        if missing:
            raise ValueError(f"Step for '{component_type}' missing required field(s): {', '.join(missing)}")
        
        params = params_raw
    else: # Actuator
        params = {k: v for k, v in step.items() if k != component_type_key}

    return component_type, params

# -------- Engine --------
class GameSequence:
    def __init__(self, config_path: Path, input_queue: queue.Queue, output_manager: OutputManager):
        self.config_path = config_path
        self.input_queue = input_queue
        self.output_manager = output_manager
        self.config = self._load_config()
        self.stop_timer_flag = threading.Event()
        self.start_time_global = 0
        self.sensor_state = {}

    def _load_config(self):
        with open(self.config_path, 'r') as f:
            return json.load(f)

    def _check_event(self, event: InputEvent, step: dict) -> bool:
        """
        Generic function to check if an event matches a sensor step.
        """
        sensor_type = step.get("sensor")
        
        if event.device_type != sensor_type:
            print(f"{Fore.LIGHTBLACK_EX}Ignoring event: expected sensor type '{sensor_type}', but got '{event.device_type}'.{Fore.RESET}")
            return False

        expected_params = copy.deepcopy(step)
        expected_params.pop("sensor", None)

        for key, expected_value in expected_params.items():
            actual_value = event.meta.get(key, None)
            
            if key in ["value"]:
                actual_value = event.value
            
            if actual_value != expected_value:
                print(f"{Fore.LIGHTBLACK_EX}Ignoring event: {sensor_type} requires {key} to be {expected_value}, but got {actual_value}.{Fore.RESET}")
                return False

        return True


    def _route_error(self, error_path: str):
        handler = ERROR_HANDLERS.get(error_path)
        if handler:
            handler()
        else:
            print(f"{Fore.RED}💥 Game Over!{Fore.RESET}")

    def timer_thread_func(self, time_limit: int):
        self.start_time_global = time.time()
        
        while not self.stop_timer_flag.is_set():
            remaining = time_limit - (time.time() - self.start_time_global)
            
            if remaining <= 0:
                print(f"{Fore.RED}\n⏰ Time's up!{Fore.RESET}")
                self.stop_timer_flag.set()
                self._route_error("game_over")
                break
            
            time.sleep(1)

    # def run_path(self, solution_sequence, effects, time_limit, retry_limit, death_text):
    #     print(f"▶ Starting Path. Retry limit: {retry_limit}")

    #     attempt = 1
    #     retries_left = retry_limit

    #     while retries_left > 0:
    #         print(f"\n🔁 Attempt {attempt}/{retry_limit}")
    #         self.sensor_state = {}

    #         # Start timer thread
    #         self.stop_timer_flag.clear()
    #         self.start_time_global = time.time()
    #         timer_thread = threading.Thread(target=self.timer_thread_func, args=(time_limit,))
    #         timer_thread.daemon = True
    #         timer_thread.start()

    #         # Send initial effects to the OutputManager
    #         for effect in effects:
    #             try:
    #                 actuator_type, params = _normalize_and_validate_step(effect)
    #                 self.output_manager.command_queue.put((actuator_type, params))
    #             except Exception as e:
    #                 print(f"✖ Invalid initial effect: {e}")
            
    #         sequence_success = True
    #         for idx, step in enumerate(solution_sequence, start=1):
    #             # Timed out
    #             if self.stop_timer_flag.is_set():
    #                 sequence_success = False
    #                 return False

    #             try:
    #                 if "sensor" in step:
    #                     expected_sensor_type, params = _normalize_and_validate_step(step)
    #                     print(f"{Fore.LIGHTCYAN_EX}Step {idx}: Waiting for sensor '{expected_sensor_type}' with value: {params.get('value')}...{Style.RESET_ALL}")

    #                     while True:
    #                         if self.stop_timer_flag.is_set():
    #                             sequence_success = False
    #                             return False
                            
    #                         try:
    #                             event = self.input_queue.get(timeout=0.1)
    #                             if self._check_event(event, step):
    #                                 print(f"{Fore.GREEN}✅ Correct sensor activation!{Style.RESET_ALL}")
    #                                 break
                                
    #                         except queue.Empty:
    #                             pass
                                
    #                 elif "actuator" in step:
    #                     actuator_type, params = _normalize_and_validate_step(step)
                        
    #                     print(f"➡ Step {idx}: Actuator {actuator_type} {params}")
    #                     self.output_manager.command_queue.put((actuator_type, params))
                        
    #             except Exception as e:
    #                 print(f"{Fore.YELLOW}✖ Invalid step #{idx}: {e}{Style.RESET_ALL}")
    #                 sequence_success = False
    #                 break
            
    #         self.stop_timer_flag.set()

    #         if sequence_success:
    #             print(f"{Fore.GREEN}\n✅ Success! Sequence completed.{Style.RESET_ALL}")
    #             return True
    #         else:
    #             retries_left -= 1
    #             if retries_left <= 0:
    #                 self._route_error(death_text if death_text else "game_over")
    #                 return False
    #             else:
    #                 print(f"✖ Incorrect sequence. Retries left: {retries_left}/{retry_limit}")
    #                 attempt += 1
    #                 while not self.input_queue.empty():
    #                     self.input_queue.get()


    def run_sequence(self):
        title = self.config.get("title", "Untitled Room")
        starting_description = self.config.get("starting_description", "")
        paths = self.config.get("paths", [])

        print(f"{Fore.MAGENTA}=== {title} ==={Fore.RESET}")
        print(f"\n{Fore.MAGENTA}--- {starting_description} ---{Fore.RESET}")
        
        # Iterate through each path in the configuration
        for i, path in enumerate(paths):
            path_name = path.get("path_name", f"Path {i+1}")
            # ... (getting other path variables remains the same) ...
            description = path.get("description", "")
            hint = path.get("hint", "")
            solution_sequence = path.get("solution_sequence", [])
            effects = path.get("effects", [])
            time_limit = path.get("time_limit", 90)
            retry_limit = int(path.get("retry_limit", 3))
            death_text = path.get("death_text", "")

            print(f"\n{Fore.MAGENTA}--- {path_name} ---{Fore.RESET}")
            print(f"{description}")
            print(f"\n{Fore.YELLOW}💡 Hint: {hint}{Fore.RESET}")

            if not solution_sequence:
                raise ValueError("No solution_sequence defined.")

            # --- Logic for a single path ---
            path_succeeded = False
            retries_left = retry_limit

            while retries_left > 0:
                print(f"\n🔁 Attempt {retry_limit - retries_left + 1}/{retry_limit}")
                
                # This is a placeholder for your inner sequence logic
                # For this to work, this inner logic must return True or False
                sequence_success = self._run_single_attempt(solution_sequence, time_limit, effects)

                if sequence_success:
                    # 1. If the attempt was successful, mark the path as succeeded...
                    path_succeeded = True
                    print(f"{Fore.GREEN}\n✅ Success! Path '{path_name}' completed.{Style.RESET_ALL}")
                    # 2. ...and 'break' out of the 'while' loop to go to the next path.
                    break 
                else:
                    retries_left -= 1
                    if retries_left > 0:
                        print(f"✖ Incorrect sequence. Retries left: {retries_left}/{retry_limit}")
                    else:
                        print(f"{Fore.RED}\nNo retries left for '{path_name}'.{Style.RESET_ALL}")

            # 3. After the 'while' loop, check if this path was ever solved.
            if not path_succeeded:
                # If a path is failed, end the entire game.
                self._route_error(death_text if death_text else "game_over")
                return False # Exit the function with a failure status

        # 4. If the 'for' loop completes without any failures, the game is won.
        print(f"{Fore.GREEN}\n🎉 Congratulations! All paths completed!{Style.RESET_ALL}")
        return True

    # You need a helper method to contain the logic for a single attempt.
    # This makes the main loop much easier to read and manage.
    def _run_single_attempt(self, solution_sequence, time_limit, effects):
        self.sensor_state = {}

        # Start timer thread
        self.stop_timer_flag.clear()
        self.start_time_global = time.time()
        timer_thread = threading.Thread(target=self.timer_thread_func, args=(time_limit,))
        timer_thread.daemon = True
        timer_thread.start()

        # Send initial effects to the OutputManager
        for effect in effects:
            try:
                actuator_type, params = _normalize_and_validate_step(effect)
                self.output_manager.command_queue.put((actuator_type, params))
            except Exception as e:
                print(f"✖ Invalid initial effect: {e}")
        
        sequence_success = True
        for idx, step in enumerate(solution_sequence, start=1):
            if self.stop_timer_flag.is_set():
                sequence_success = False
                break

            try:
                if "sensor" in step:
                    expected_sensor_type, params = _normalize_and_validate_step(step)
                    print(f"{Fore.LIGHTCYAN_EX}Step {idx}: Waiting for sensor '{expected_sensor_type}' with value: {params.get('value')}...{Style.RESET_ALL}")
                    
                    # Inner loop for waiting on a single sensor event
                    while True: 
                        if self.stop_timer_flag.is_set():
                            sequence_success = False
                            break
                        try:
                            event = self.input_queue.get(timeout=0.1)
                            if self._check_event(event, step):
                                print(f"{Fore.GREEN}✅ Correct sensor activation!{Style.RESET_ALL}")
                                break # Correct event, break from waiting loop
                        except queue.Empty:
                            continue # No event, continue waiting
                    
                    if not sequence_success: # Break outer loop if timer ran out
                        break

                elif "actuator" in step:
                    actuator_type, params = _normalize_and_validate_step(step)
                    print(f"➡ Step {idx}: Actuator {actuator_type} {params}")
                    self.output_manager.command_queue.put((actuator_type, params))
                    
            except Exception as e:
                print(f"{Fore.YELLOW}✖ Invalid step #{idx}: {e}{Style.RESET_ALL}")
                sequence_success = False
                break
        
        self.stop_timer_flag.set()
        timer_thread.join() # Wait for timer thread to finish
        
        # Clear input queue for next attempt
        while not self.input_queue.empty():
            self.input_queue.get()

        return sequence_success