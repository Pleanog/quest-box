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
    def __init__(self, config_path: Path, input_queue: queue.Queue, output_manager: OutputManager, game_name: str):
        self.config_path = config_path
        self.input_queue = input_queue
        self.output_manager = output_manager
        self.game_name = game_name
        self.config = self._load_config()
        self.stop_timer_flag = threading.Event()
        self.start_time_global = 0
        self.sensor_state = {}
        # Stores the text of the last spoken/printed description or hint
        self.last_spoken_text = ""

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


    def _play_audio(self, text: str, audio_file_name: str, repeat: bool = False):
        """Plays an audio file and sets the last spoken text."""
        
        # 1. Update last spoken text regardless of success
        self.last_spoken_text = text
        
        # 2. Console output
        if repeat:
            print(f"{Fore.CYAN}🔁 (Repeat) {text}{Fore.RESET}")
        else:
            print(f"\n{Fore.MAGENTA}--- Description/Hint ---{Fore.RESET}")
            print(text)
            
        # 3. Audio Command (Assuming audio files are in a game-specific folder)
        # Note: You may need to adjust the command details based on your OutputManager implementation.
        # This assumes the file is already generated and located in the game's audio folder.
        full_audio_path = f"game/{self.game_name}/audio/{audio_file_name}"
        self.output_manager.command_queue.put(("sound", {"file": full_audio_path}))


    def run_sequence(self):
        """The main entry point to start the game."""
        title = self.config.get("title", "Untitled Room")
        starting_description = self.config.get("starting_description", "")
        paths = self.config.get("paths", [])

        print(f"{Fore.MAGENTA}=== {title} ==={Fore.RESET}")
        
        # Initial description is played/printed
        self._play_audio(starting_description, "starting_description.mp3")
        time.sleep(2) # Give audio time to start

        for i, path in enumerate(paths):
            path_succeeded = self._run_single_path(path)
            if not path_succeeded:
                print(f"{Fore.RED}\nGame Over. Failed to complete the quest.{Style.RESET_ALL}")
                return False # End the game

        print(f"{Fore.GREEN}\n🎉 Congratulations! All paths completed!{Style.RESET_ALL}")
        return True

    def _run_single_path(self, path_config):
        """Manages the logic for a single path, including the wait/hint/repeat loop."""
        path_name = path_config.get("path_name", "Unknown Path")
        description = path_config.get("description", "")
        hint = path_config.get("hint", "")
        # solution_sequence = path_config.get("solution_sequence", []) # Not needed anymore here i think
        
        # 1. Play the path description
        print(f"\n{Fore.MAGENTA}--- Starting Path: {path_name} ---{Fore.RESET}")
        self._play_audio(description, f"{path_name.replace(' ', '_').lower()}_description.mp3")

        # 2. Wait for a valid input (puzzle solution OR hint/repeat button)
        first_event = None
        while True:
            try:
                # Wait for player input. You might adjust the timeout.
                event = self.input_queue.get(timeout=600) 
                
                # Check for special commands
                if event.device_type == "button" and event.value == "repeat":
                    # Re-play the last spoken description
                    # We reuse the last spoken text and rely on audio generator's caching/lookup.
                    if self.last_spoken_text:
                        # Find the correct filename for the last spoken text. 
                        # We re-play the path description's audio file, 
                        
                        # --- OPTION A: REPEAT THE DESCRIPTION AUDIO FILE ---
                        audio_filename_to_repeat = f"{path_name.replace(' ', '_').lower()}_description.mp3"
                        self._play_audio(description, audio_filename_to_repeat, repeat=True)
                        
                    else:
                        print(f"{Fore.RED}No recent audio to repeat.{Fore.RESET}")
                    continue
                
                if event.device_type == "button" and event.value == "hint":
                    # Play the hint
                    self._play_audio(hint, f"{path_name.replace(' ', '_').lower()}_hint.mp3")
                    continue
                
                # If it's not a special command, it's the start of the puzzle attempt.
                first_event = event
                break

            except queue.Empty:
                print("No input received. Are you still there? (Timeout occurred)")
                # If timeout is hit, we break to the failure path or end the game
                return False # End the path/game on a prolonged timeout

        # 3. Once the wait loop is broken, start the timed attempts
        retry_limit = int(path_config.get("retry_limit", 3))
        retries_left = retry_limit

        while retries_left > 0:
            print(f"\n🔁 Attempt {retry_limit - retries_left + 1}/{retry_limit}")
            
            # Pass the first event that started the sequence
            attempt_success = self._run_single_attempt(path_config, first_event)
            
            # After the first attempt, the first_event is used up
            first_event = None 

            if attempt_success:
                print(f"{Fore.GREEN}\n✅ Success! Path '{path_name}' completed.{Style.RESET_ALL}")
                return True 
            
            retries_left -= 1
            if retries_left > 0:
                print(f"✖ Incorrect sequence. Retries left: {retries_left}/{retry_limit}")
            else:
                death_text = path_config.get("death_text", "You have failed.")
                self._play_audio(death_text, f"{path_name.replace(' ', '_').lower()}_death.mp3")
                self._route_error(death_text)

        return False # All retries failed for this path

    def _run_single_attempt(self, path_config, first_event=None):
        """Executes one timed attempt of a solution sequence."""
        solution_sequence = path_config.get("solution_sequence", [])
        time_limit = path_config.get("time_limit", 90)
        effects = path_config.get("effects", [])

        # Send initial effects to the OutputManager
        for effect in effects:
            try:
                actuator_type, params = _normalize_and_validate_step(effect)
                self.output_manager.command_queue.put((actuator_type, params))
            except Exception as e:
                print(f"✖ Invalid initial effect: {e}")

        self.stop_timer_flag.clear()
        timer_thread = threading.Thread(target=self.timer_thread_func, args=(time_limit,))
        timer_thread.start()

        sequence_success = True
        for idx, step in enumerate(solution_sequence):
            if self.stop_timer_flag.is_set():
                sequence_success = False
                break

            current_event = None
            if idx == 0 and first_event:
                current_event = first_event
            else:
                try:
                    current_event = self.input_queue.get(timeout=time_limit)
                except queue.Empty:
                    sequence_success = False
                    break
            
            if not self._check_event(current_event, step):
                sequence_success = False
                break
        
        self.stop_timer_flag.set()
        timer_thread.join()
        
        while not self.input_queue.empty():
            self.input_queue.get()
            
        return sequence_success
        
# import json
# import time
# import threading
# import queue
# import copy
# from pathlib import Path
# from input_manager import InputEvent
# from output_manager import OutputManager
# from colorama import Fore, Style

# #  ---- Registry --------
# SENSOR_REGISTRY = {
#     "button": {
#         "required": ["value"],
#         "aliases": {"count": "times", "presses": "times", "num": "times"},
#     },
#     "joystick": {
#         "required": ["value"],
#         "aliases": {},
#     },
#     "distance_sensor": {
#         "required": ["value"], # The states (covered, hovered, clear)
#         "aliases": {},
#     },
#     "gyro": {
#         "required": ["value"],
#         "aliases": {},
#     },
#     "rotary_encoder_number": {
#         "required": ["value"], # This is a dictionary of 10 values
#         "aliases": {},
#     },
#     "rotary_encoder_picture": {
#         "required": ["value"], # This is a dictionary of 10 values
#         "aliases": {},
#     }
# }

# # -------- Error handlers --------
# def handle_game_over():
#     print("💥 Game Over!")
    
# def handle_timeout():
#     print("⏰ Time's up!")
#     handle_game_over()
    
# ERROR_HANDLERS = {
#     "game_over": handle_game_over,
# }

# # -------- Utilities --------
# def _normalize_and_validate_step(step: dict) -> tuple[str, dict]:
#     """
#     Returns (component_type, params) after:
#       - verifying component exists
#       - applying alias mappings
#       - checking required fields
#     """
#     if "sensor" in step:
#         component_type_key = "sensor"
#         registry = SENSOR_REGISTRY
#     elif "actuator" in step:
#         component_type_key = "actuator"
#         # For actuators, we don't need a registry to validate parameters
#         # because the OutputManager now handles this.
#         registry = {}
#     else:
#         raise ValueError("Step is missing 'sensor' or 'actuator'.")
    
#     component_type = step[component_type_key]
    
#     # Validation logic specific to sensors
#     if component_type_key == "sensor":
#         if component_type not in registry:
#             raise ValueError(f"Unknown sensor component '{component_type}'.")
        
#         spec = registry[component_type]
#         aliases = spec.get("aliases", {})
#         required = spec.get("required", [])

#         params_raw = { (aliases.get(k, k)): v for k, v in step.items() if k != component_type_key }

#         missing = [k for k in required if k not in params_raw]
#         if missing:
#             raise ValueError(f"Step for '{component_type}' missing required field(s): {', '.join(missing)}")
        
#         params = params_raw
#     else: # Actuator
#         params = {k: v for k, v in step.items() if k != component_type_key}

#     return component_type, params

# # -------- Engine --------
# class GameSequence:
#     def __init__(self, config_path: Path, input_queue: queue.Queue, output_manager: OutputManager):
#         self.config_path = config_path
#         self.input_queue = input_queue
#         self.output_manager = output_manager
#         self.config = self._load_config()
#         self.stop_timer_flag = threading.Event()
#         self.start_time_global = 0
#         self.sensor_state = {}

#     def _load_config(self):
#         with open(self.config_path, 'r') as f:
#             return json.load(f)

#     def _check_event(self, event: InputEvent, step: dict) -> bool:
#         """
#         Generic function to check if an event matches a sensor step.
#         """
#         sensor_type = step.get("sensor")
        
#         if event.device_type != sensor_type:
#             print(f"{Fore.LIGHTBLACK_EX}Ignoring event: expected sensor type '{sensor_type}', but got '{event.device_type}'.{Fore.RESET}")
#             return False

#         expected_params = copy.deepcopy(step)
#         expected_params.pop("sensor", None)

#         for key, expected_value in expected_params.items():
#             actual_value = event.meta.get(key, None)
            
#             if key in ["value"]:
#                 actual_value = event.value
            
#             if actual_value != expected_value:
#                 print(f"{Fore.LIGHTBLACK_EX}Ignoring event: {sensor_type} requires {key} to be {expected_value}, but got {actual_value}.{Fore.RESET}")
#                 return False

#         return True


#     def _route_error(self, error_path: str):
#         handler = ERROR_HANDLERS.get(error_path)
#         if handler:
#             handler()
#         else:
#             print(f"{Fore.RED}💥 Game Over!{Fore.RESET}")

#     def timer_thread_func(self, time_limit: int):
#         self.start_time_global = time.time()
        
#         while not self.stop_timer_flag.is_set():
#             remaining = time_limit - (time.time() - self.start_time_global)
            
#             if remaining <= 0:
#                 print(f"{Fore.RED}\n⏰ Time's up!{Fore.RESET}")
#                 self.stop_timer_flag.set()
#                 self._route_error("game_over")
#                 break
            
#             time.sleep(1)

#     def _play_audio(self, text, audio_file_name):
#         """Plays an audio file and sets it as the last spoken text."""
#         self.last_spoken_text = text
#         # Assuming your OutputManager handles a 'tts' or 'sound' command
#         # This command should play the audio file located at a path like:
#         # games/{game_name}/audio/{audio_file_name}
#         self.output_manager.command_queue.put(("sound", {"file": audio_file_name}))

#     def run_sequence(self):
#         """The main entry point to start the game."""
#         title = self.config.get("title", "Untitled Room")
#         starting_description = self.config.get("starting_description", "")
#         paths = self.config.get("paths", [])

#         print(f"{Fore.MAGENTA}=== {title} ==={Fore.RESET}")
#         self._play_audio(starting_description, "starting_description.mp3")
#         time.sleep(2) # Give audio time to start

#         for i, path in enumerate(paths):
#             path_succeeded = self._run_single_path(path)
#             if not path_succeeded:
#                 print(f"{Fore.RED}\nGame Over. Failed to complete the quest.{Style.RESET_ALL}")
#                 return False # End the game

#         print(f"{Fore.GREEN}\n🎉 Congratulations! All paths completed!{Style.RESET_ALL}")
#         return True

#     def _run_single_path(self, path_config):
#         """Manages the logic for a single path, including the wait/hint/repeat loop."""
#         path_name = path_config.get("path_name", "Unknown Path")
#         description = path_config.get("description", "")
#         hint = path_config.get("hint", "")
#         solution_sequence = path_config.get("solution_sequence", [])
        
#         print(f"\n{Fore.MAGENTA}--- Starting Path: {path_name} ---{Fore.RESET}")
#         self._play_audio(description, f"{path_name.replace(' ', '_').lower()}_description.mp3")

#         # --- This is the new "wait for action" loop ---
#         first_event = None
#         while True:
#             try:
#                 event = self.input_queue.get(timeout=600) # Wait for player input
                
#                 # Check for special commands
#                 if event.device_type == "button" and event.value == "repeat":
#                     print(f"{Fore.CYAN}Repeat button pressed.{Style.RESET_ALL}")
#                     # Re-play the last spoken text, whatever it was
#                     self._play_audio(self.last_spoken_text, "placeholder_for_repeat.mp3") # Note: this requires a way to map text back to a filename
#                     continue
                
#                 if event.device_type == "button" and event.value == "hint":
#                     print(f"{Fore.YELLOW}Hint button pressed.{Style.RESET_ALL}")
#                     # Play the hint and set it as the last spoken text
#                     self._play_audio(hint, f"{path_name.replace(' ', '_').lower()}_hint.mp3")
#                     continue
                
#                 # If it's not a special command, it's the start of the puzzle attempt.
#                 first_event = event
#                 break

#             except queue.Empty:
#                 print("No input received. Are you still there?")
#                 continue

#         # --- Once the wait loop is broken, start the timed attempts ---
#         retry_limit = int(path_config.get("retry_limit", 3))
#         retries_left = retry_limit

#         while retries_left > 0:
#             print(f"\n🔁 Attempt {retry_limit - retries_left + 1}/{retry_limit}")
            
#             # Pass the first event that started the sequence
#             attempt_success = self._run_single_attempt(path_config, first_event)
            
#             # After the first attempt, the first_event is used up
#             first_event = None 

#             if attempt_success:
#                 print(f"{Fore.GREEN}\n✅ Success! Path '{path_name}' completed.{Style.RESET_ALL}")
#                 return True # This path is done, return True
            
#             retries_left -= 1
#             if retries_left > 0:
#                 print(f"✖ Incorrect sequence. Retries left: {retries_left}/{retry_limit}")
#             else:
#                 death_text = path_config.get("death_text", "You have failed.")
#                 self._play_audio(death_text, f"{path_name.replace(' ', '_').lower()}_death.mp3")
#                 self._route_error(death_text)

#         return False # All retries failed for this path

#     def _run_single_attempt(self, path_config, first_event=None):
#         """Executes one timed attempt of a solution sequence."""
#         solution_sequence = path_config.get("solution_sequence", [])
#         time_limit = path_config.get("time_limit", 90)
#         effects = path_config.get("effects", [])

#         # Send initial effects to the OutputManager
#         for effect in effects:
#             try:
#                 actuator_type, params = _normalize_and_validate_step(effect)
#                 self.output_manager.command_queue.put((actuator_type, params))
#             except Exception as e:
#                 print(f"✖ Invalid initial effect: {e}")

#         # ... [The code for starting timer and effects is the same] ...
#         self.stop_timer_flag.clear()
#         timer_thread = threading.Thread(target=self.timer_thread_func, args=(time_limit,))
#         timer_thread.start()

#         sequence_success = True
#         for idx, step in enumerate(solution_sequence):
#             if self.stop_timer_flag.is_set():
#                 sequence_success = False
#                 break

#             current_event = None
#             if idx == 0 and first_event:
#                 # Use the event that broke the wait loop for the first step
#                 current_event = first_event
#             else:
#                 # For all other steps, get a new event
#                 try:
#                     current_event = self.input_queue.get(timeout=time_limit)
#                 except queue.Empty:
#                     sequence_success = False
#                     break
            
#             # Check the event against the current step
#             if not self._check_event(current_event, step):
#                 sequence_success = False
#                 break
        
#         self.stop_timer_flag.set()
#         timer_thread.join()
        
#         while not self.input_queue.empty():
#             self.input_queue.get()
            
#         return sequence_success
