# main.py (Updated)

# # ! ---------------------------
# # ! Needs to run with sudo !!!!
# # ! because of led controller !
# # ! ---------------------------

import sys
import os
import time
import pygame
from pathlib import Path
from threading import Thread
from queue import Queue

# Append parent directory to sys.path to resolve local imports (as per your original setup)
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

# Import shared service setup (assuming your elevenlabsAPI folder/files are correctly named)
from geminiAPI.gemini_client import generate_room_configuration
from elevenlabsAPI.tts_service import TTSService 
from game_audio_generator import GameAudioGenerator
from filename_service import FileNameService

# Import Core Game Components
from game_sequence import GameSequence
from input_manager import InputManager
from output_manager import OutputManager
from led_controller import LEDController
from sound_controller import SoundController 
from vibration_motor_controller import VibrationController
from bus_manager import I2C_BUS_LOCK

# Import the new Menu Manager
from menu_manager import MenuManager 

BASE_DIR = Path(__file__).parent.parent


def main():
    try:
        # pygame.init()  # Initialize Pygame

        # --- 1. INITIALIZE THREAD MANAGERS (needed for menu input/output) ---
        print("--- 1. Initializing System Components ---")
        
        # Queues for inter-thread communication
        input_event_queue = Queue()
        output_command_queue = Queue()

        # Initialize Services
        audio_service = TTSService(str(BASE_DIR)) # TTS for menu audio
        
        # Initialize Controllers
        led_controller = LEDController()
        vibration_controller = VibrationController()
        file_service = FileNameService(str(BASE_DIR)) # <-- Needs to be defined before SoundController
        sound_controller = SoundController(file_service) # TTS for game audio

        # Add controllers to the OutputManager
        output_manager_instance = OutputManager(output_command_queue)
        output_manager_instance.add_controller("light", led_controller)
        output_manager_instance.add_controller("vibration", vibration_controller)
        output_manager_instance.add_controller("tts_service", audio_service)
        output_manager_instance.add_controller("sound", sound_controller)

        # Define device configurations (Hint and Repeat are crucial here)
        device_configs = [
            {"type": "sx1509_button", "value": "repeat", "pin": 11}, # MENU SWITCH GAME/REPEAT
            {"type": "sx1509_button", "value": "hint", "pin": 3}, # MENU START GAME/HINT
            {"type": "sx1509_button", "value": "yellow", "pin": 4},
            {"type": "sx1509_button", "value": "red", "pin": 1},
            {"type": "sx1509_button", "value": "green", "pin": 14},
            {"type": "sx1509_button", "value": "blue", "pin": 13},
            {"type": "gyro", "value": "shaking"},
            {"type": "rotary_encoder", "name": "rotary_encoder_picture", "clk_pin": 20, "dt_pin": 21, "button_pin": 16},
            {"type": "rotary_encoder", "name": "rotary_encoder_number", "clk_pin": 13, "dt_pin": 19, "button_pin": 26},
            {"type": "distance_sensor", "trigger_pin": 23, "echo_pin": 24},
        ]

        # Initialize Input Manager
        input_manager_instance = InputManager(input_event_queue, bus_lock=I2C_BUS_LOCK, device_configs=device_configs)

        # Add devices to the Input Manager
        for config in device_configs:
            input_manager_instance.add_device(config)
        
        # Start the Input and Output Managers in separate threads
        input_thread = Thread(target=input_manager_instance.start)
        input_thread.daemon = True
        input_thread.start()

        output_thread = Thread(target=output_manager_instance.start)
        output_thread.daemon = True
        output_thread.start()
        
        time.sleep(1) # Give threads time to initialize

        # --- 2. RUN MENU LOOP ---
        menu_manager = MenuManager(input_event_queue, output_manager_instance, file_service)
        # The menu manager will return the selected game name or the GENERATE_NEW_GAME signal
        selected_game_name = menu_manager.run_menu()

        # --- 3. LOAD/GENERATE GAME CONFIG ---
        game_name = None
        if selected_game_name == MenuManager.GENERATE_NEW_GAME:
            print("--- 3. Generating New Game via Gemini ---")
            game_name = generate_room_configuration()
            if not game_name:
                print("FATAL ERROR: Failed to generate a new room configuration. Exiting.")
                return
            
            # Audio generation runs ONLY for newly generated games
            audio_generator = GameAudioGenerator(str(BASE_DIR), audio_service)
            audio_success = audio_generator.generate_all_game_audio(game_name)
            
            if not audio_success:
                print("Warning: Some audio files failed to generate. Continuing with available files.")
        else:
            # Load a pre-existing game
            game_name = selected_game_name
            print(f"--- 3. Loading Saved Game: {game_name} ---")

        # --- 4. START GAME SEQUENCE ---
        print(f"Starting game sequence for: {game_name}")
        
        # Initialize Game Sequence
        config_path = file_service.get_game_json_path(game_name)
        game_sequence_instance = GameSequence(
            config_path=config_path,
            input_queue=input_event_queue,
            output_manager=output_manager_instance,
            game_name=game_name,
        )

        print("Starting game loop...")
        game_sequence_instance.run_sequence()
    except (KeyboardInterrupt, RuntimeError) as e:
        # Catch Ctrl+C or our custom runtime error
        print(f"\nExiting due to: {e}")
    finally:
        # --- THIS CLEANUP CODE IS NOW GUARANTEED TO RUN ---
        print("--- Shutting down all systems ---")
        if input_manager_instance:
            input_manager_instance.stop()
        if output_manager_instance:
            output_manager_instance.stop()
        
        # This will now always be called
        print("Shutting down Pygame mixer...")
        pygame.quit() 
        print("Exited cleanly.")

if __name__ == "__main__":
    main()
