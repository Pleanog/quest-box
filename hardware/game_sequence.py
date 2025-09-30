import json
import time
import threading
import queue
import copy
import pygame
from pathlib import Path
from input_manager import InputEvent
from output_manager import OutputManager
# from filename_service import FileNameService
from colorama import Fore, Style

pygame.mixer.init()

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
    def __init__(self, config_path: Path, input_queue: queue.Queue, output_manager: OutputManager, game_name: str,):
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
        self.last_audio_filename = ""

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

    def _play_audio_and_wait(self, text: str, audio_type: str, path_identifier: str):
        """
        Sends a command to play audio and BLOCKS until the audio has finished playing.
        """
        print(text)
        
        self.output_manager.command_queue.put(
            ("sound", {
                "type_prefix": audio_type, 
                "path_name": path_identifier,
                "game_name": self.game_name,
                "loop": False
            })
        )
        print(f"{Style.DIM}--- GameSequence: Audio command for '{audio_type}' sent. Waiting... ---{Style.RESET_ALL}")

        # Wait for the audio to START playing
        started = False
        print(f"{Style.DIM}  - Waiting for sound to START...{Style.RESET_ALL}")
        for i in range(30):
            if pygame.mixer.music.get_busy():
                print(f"{Style.DIM}  - Sound has STARTED. (after {i * 0.1:.1f}s){Style.RESET_ALL}")
                started = True
                break
            time.sleep(0.1)

        if not started:
            print(f"{Fore.YELLOW}Warning: Sound did not start playing within the time limit.{Style.RESET_ALL}")
            return

        # Wait for the audio to FINISH playing
        print(f"{Style.DIM}  - Waiting for sound to FINISH...{Style.RESET_ALL}")
        while pygame.mixer.music.get_busy():
            time.sleep(0.1)
        print(f"{Style.DIM}  - Sound has FINISHED.{Style.RESET_ALL}")

    def _play_audio_non_blocking(self, text: str, audio_type: str, path_identifier: str, repeat: bool = False):
        """
        Sends a command to play audio but does NOT block. Used for hints, repeats, etc.
        """
        if repeat:
            print(f"{Fore.CYAN}🔁 (Repeat) Playing: {audio_type} for {path_identifier}{Fore.RESET}")
        else:
            print(text)
        
        # Send the command and return immediately
        self.output_manager.command_queue.put(
            ("sound", {
                "type_prefix": audio_type, 
                "path_name": path_identifier,
                "game_name": self.game_name,
                "loop": False
            })
        )

    # def _wait_for_audio_to_finish(self):
    #     """Pauses the game sequence while the sound controller is busy."""
    #     # This gives a brief moment for the command to reach the sound thread
    #     time.sleep(0.2) 
    #     while pygame.mixer.music.get_busy():
    #         time.sleep(0.1) # Wait in small intervals

    # def _play_audio(self, text: str, audio_type: str, path_identifier: str, repeat: bool = False):
    #     """
    #     Plays an audio file by sending type and identifier to the SoundController.
        
    #     Args:
    #         text (str): The text content (for console output and last spoken record).
    #         audio_type (str): The type of audio ('starting_description', 'description', 'hint', 'death_text').
    #         path_identifier (str): The name of the path (or game_name for starting text).
    #         repeat (bool): Whether this is a repeat command.
    #     """
    #     self.last_spoken_text = text
        
    #     # NOTE: We no longer store last_audio_filename, as the SoundController now computes it.
    #     # self.last_audio_filename = audio_file_name 
        
    #     if repeat:
    #         # We don't print the full text on repeat, just the action
    #         print(f"{Fore.CYAN}🔁 (Repeat) Playing: {audio_type} for {path_identifier}{Fore.RESET}")
    #     else:
    #         print(text)
            
    #     # Send the command with all necessary descriptive elements
    #     self.output_manager.command_queue.put(
    #         ("sound", {
    #             "type_prefix": audio_type, 
    #             "path_name": path_identifier, # e.g., 'The Sheriffs Safe' or 'the-sheriffs-safe'
    #             "game_name": self.game_name,   # e.g., 'the-sheriffs-safe'
    #             "loop": False                  # Assuming playback is not looping here
    #         })
    #     )

    def run_sequence(self):
        """The main entry point to start the entire game quest."""
        title = self.config.get("title", "Untitled Room")
        starting_description = self.config.get("starting_description", "")
        paths = self.config.get("paths", [])

        print(f"{Fore.MAGENTA}=== {title} ==={Fore.RESET}")
        self._play_audio_and_wait(starting_description, "starting_description", self.game_name)

        for path in paths:
            path_succeeded = self._run_single_path(path)
            if not path_succeeded:
                # The death text and error are handled inside _run_single_path
                return False # End the game

        print(f"{Fore.GREEN}\n🎉 Congratulations! All paths completed!{Style.RESET_ALL}")
        return True

    def _run_single_path(self, path_config):
        """
        Runs the logic for a single, timed path with infinite attempts and
        persistent hint/repeat commands.
        """
        # --- 1. SETUP THE PATH ---
        path_name = path_config.get("path_name", "Unknown Path")
        description = path_config.get("description", "")
        hint = path_config.get("hint", "")
        solution_sequence = path_config.get("solution_sequence", [])
        time_limit = path_config.get("time_limit", 90)
        death_text = path_config.get("death_text", "You have failed.")
        effects = path_config.get("effects", [])

        # Used to track progress through the solution_sequence
        current_step_index = 0

        # --- 2. START THE PATH ---
        print(f"\n{Fore.MAGENTA}--- Starting Path: {path_name} ---{Fore.RESET}")
        
        # Play initial effects
        for effect in effects:
            try:
                actuator_type, params = _normalize_and_validate_step(effect)
                self.output_manager.command_queue.put((actuator_type, params))
            except Exception as e:
                print(f"✖ Invalid initial effect: {e}")
        
        # Play the path description and start the timer
        self._play_audio_and_wait(description, "description", path_name)
        self.stop_timer_flag.clear()
        timer_thread = threading.Thread(target=self.timer_thread_func, args=(time_limit,))
        timer_thread.daemon = True
        timer_thread.start()
        print(f"{Fore.CYAN}Timer started! You have {time_limit} seconds.{Style.RESET_ALL}")

        # --- 3. THE MAIN GAME LOOP ---
        while current_step_index < len(solution_sequence):
            # Check for timeout first on every loop iteration
            if self.stop_timer_flag.is_set():
                self._play_audio_non_blocking(death_text, "death_text", path_name)
                self._route_error(death_text)
                return False

            try:
                # Use a short timeout to remain responsive to the timer flag
                event = self.input_queue.get(timeout=0.1)

                # --- PROCESS SPECIAL COMMANDS (HINT/REPEAT) ---
                if event.device_type == "button" and event.value == "repeat":
                    self._play_audio_non_blocking(hint, "hint", path_name)
                    continue # Go back to waiting for the next event

                if event.device_type == "button" and event.value == "hint":
                    self._play_audio_non_blocking(hint, "hint", path_name)
                    continue # Go back to waiting for the next event

                # --- PROCESS PUZZLE INPUT ---
                expected_step = solution_sequence[current_step_index]
                if self._check_event(event, expected_step):
                    current_step_index += 1
                    print(f"{Fore.GREEN}✅ Step {current_step_index} correct!{Style.RESET_ALL}")
                else:
                    # Incorrect input, do nothing and wait for the correct one
                    print(f"{Fore.YELLOW}✖ Incorrect input. Try again.{Style.RESET_ALL}")
            
            except queue.Empty:
                # This is normal, it just means no input was received. Loop again.
                continue

        # --- 4. PATH SUCCESS ---
        self.stop_timer_flag.set() # Stop the timer
        timer_thread.join()
        print(f"{Fore.GREEN}\n✅ Success! Path '{path_name}' completed.{Style.RESET_ALL}")
        return True
    

# game_sequence.py

# ... (all of your existing GameSequence class code) ...


# ==================================================================
# =================== SELF-CONTAINED TEST HARNESS ==================
# ==================================================================
if __name__ == "__main__":
    # This block will only run when you execute `python game_sequence.py` directly

    # --- 1. MOCK CLASSES (Fake versions of your other managers) ---
    # We create simple versions of the other classes to satisfy the dependencies.

    class MockFileNameService:
        """A fake FileNameService for testing."""
        def __init__(self, base_dir):
            self.base_dir = Path(base_dir)

        def get_audio_filename(self, type_prefix: str, path_name: str) -> str:
            clean_path = path_name.lower().replace(" ", "_").replace("-", "_")
            return f"{type_prefix}_{clean_path}.mp3"

        def get_audio_folder_path(self, game_name: str) -> str:
            return str(self.base_dir / "games" / game_name / "audio")
            
        def get_game_json_path(self, game_name: str) -> str:
            return str(self.base_dir / "games" / game_name / f"{game_name}.json")


    class MockSoundController:
        """A fake SoundController that directly uses Pygame."""
        def __init__(self, file_service):
            self.file_service = file_service
        
        def set_effect(self, **params):
            # This logic is copied from your real SoundController
            try:
                file_name = self.file_service.get_audio_filename(params['type_prefix'], params['path_name'])
                folder = self.file_service.get_audio_folder_path(params['game_name'])
                path = Path(folder) / file_name
                
                if not path.exists():
                    print(f"{Fore.RED}TEST ERROR: MockSoundController could not find file: {path}{Style.RESET_ALL}")
                    return

                pygame.mixer.music.stop()
                pygame.mixer.music.load(str(path))
                pygame.mixer.music.play(-1 if params.get('loop', False) else 0)
                print(f"{Fore.GREEN}🔊 (Mock) Playing: {path.name}{Style.RESET_ALL}")
            except Exception as e:
                print(f"{Fore.RED}TEST ERROR: MockSoundController failed: {e}{Style.RESET_ALL}")

    class MockOutputManager:
        """A fake OutputManager that runs in a thread, just like the real one."""
        def __init__(self, command_queue):
            self.command_queue = command_queue
            self.controllers = {}
            self.running = False
            self.worker_thread = None

        def add_controller(self, name, controller):
            self.controllers[name] = controller

        def start(self):
            self.running = True
            self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
            self.worker_thread.start()
            print("MockOutputManager started.")

        def stop(self):
            self.running = False
            if self.worker_thread:
                self.worker_thread.join()
            print("MockOutputManager stopped.")

        def _worker_loop(self):
            while self.running:
                try:
                    name, params = self.command_queue.get(timeout=0.1)
                    if name in self.controllers:
                        self.controllers[name].set_effect(**params)
                    self.command_queue.task_done()
                except queue.Empty:
                    pass
    
    # --- 2. TEST CONFIGURATION ---
    # Change this to the game you want to test
    TEST_GAME_NAME = "the-curse-of-the-krakens-chest"
    BASE_DIR = Path(__file__).parent.parent
    
    # --- 3. TEST EXECUTION ---
    # We wrap everything in a try...finally block to ensure Pygame always quits
    
    output_manager = None
    try:
        # Initialize Pygame
        pygame.init()
        print(f"{Fore.YELLOW}--- GameSequence Audio Test ---{Style.RESET_ALL}")
        
        # Create all the necessary objects
        input_q = queue.Queue()
        output_q = queue.Queue()
        
        file_service = MockFileNameService(str(BASE_DIR))
        sound_controller = MockSoundController(file_service)
        
        output_manager = MockOutputManager(output_q)
        output_manager.add_controller("sound", sound_controller)
        output_manager.start()
        
        config_path = file_service.get_game_json_path(TEST_GAME_NAME)
        
        if not Path(config_path).exists():
            raise FileNotFoundError(f"Test requires a valid game JSON at: {config_path}")

        # Create the GameSequence instance
        game = GameSequence(
            config_path=config_path,
            input_queue=input_q,
            output_manager=output_manager,
            game_name=TEST_GAME_NAME
        )
        
        # Run the game sequence!
        game.run_sequence()
        
    except (KeyboardInterrupt, Exception) as e:
        print(f"\n{Fore.RED}Test stopped due to an error: {e}{Style.RESET_ALL}")
        
    finally:
        # This cleanup code is GUARANTEED to run
        print(f"{Fore.YELLOW}--- Test Finished ---{Style.RESET_ALL}")
        if output_manager:
            output_manager.stop()
        
        pygame.quit()
        print("Pygame shut down cleanly.")