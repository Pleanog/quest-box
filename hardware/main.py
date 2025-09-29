# # ! ---------------------------
# # ! Needs to run with sudo !!!!
# # ! because of led controller !
# # ! ---------------------------

# main.py

import sys
import os
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)
from geminiAPI.gemini_client import generate_room_configuration

from pathlib import Path
from threading import Thread
from queue import Queue
from game_sequence import GameSequence
from input_manager import InputManager
from output_manager import OutputManager
from led_controller import LEDController
from vibration_motor_controller import VibrationController
from bus_manager import I2C_BUS_LOCK

from geminiAPI.gemini_client import generate_room_configuration
from elevenlabsAPI.tts_service import AudioService
from game_audio_generator import GameAudioGenerator
from filename_service import FileNameService

BASE_DIR = Path(__file__).parent.parent

def main():
    # --- 1. GAME GENERATION AND AUDIO PREP ---
    print("--- 1. Initializing Game Generation ---")
    
    # 1. Call Gemini API to generate the game JSON
    # This returns the file-safe name (e.g., 'the-krakens-cache')
    game_name = generate_room_configuration()
    
    if not game_name:
        print("FATAL ERROR: Failed to generate a new room configuration. Exiting.")
        return

    # 2. Initialize Services needed for Audio Generation/Playback
    file_service = FileNameService(str(BASE_DIR))
    audio_service = AudioService() # Uses the ELEVEN_API_KEY from .env
    
    # 3. Generate all audio files for the new game
    audio_generator = GameAudioGenerator(str(BASE_DIR), audio_service)
    audio_success = audio_generator.generate_all_game_audio(game_name)
    
    if not audio_success:
        print("Warning: Some audio files failed to generate. Continuing with available files.")
        
    # --- 2. START GAME THREADS ---
    print("--- 2. Starting Game System ---")

    # Queues for inter-thread communication
    input_event_queue = Queue()
    output_command_queue = Queue()

    # Initialize Controllers
    led_controller = LEDController()
    vibration_controller = VibrationController()

    # Add controllers to the OutputManager
    output_manager_instance = OutputManager(output_command_queue)
    output_manager_instance.add_controller("light", led_controller)
    output_manager_instance.add_controller("vibration", vibration_controller)
    output_manager_instance.add_controller("tts_service", audio_service)
    # output_manager_instance.add_controller("sound", sound_controller)

    # Define device configurations
    device_configs = [
        {"type": "sx1509_button", "value": "red", "pin": 2},
        {"type": "sx1509_button", "value": "blue", "pin": 12},
        {"type": "sx1509_button", "value": "yellow", "pin": 4},
        {"type": "sx1509_button", "value": "green", "pin": 5},
        {"type": "sx1509_button", "value": "black", "pin": 13},
        {"type": "gyro", "value": "shaking"},
        {"type": "rotary_encoder", "name": "rotary_encoder_picture", "clk_pin": 20, "dt_pin": 21, "button_pin": 16},
        {"type": "rotary_encoder", "name": "rotary_encoder_number", "clk_pin": 13, "dt_pin": 19, "button_pin": 26},
        {"type": "distance_sensor", "trigger_pin": 23, "echo_pin": 24},
    ]

    # Initialize Managers, passing the necessary queues
    # input_manager_instance = InputManager(input_event_queue)
    input_manager_instance = InputManager(input_event_queue, bus_lock=I2C_BUS_LOCK, device_configs=device_configs)

    # Add devices to the Input Manager
    for config in device_configs:
        input_manager_instance.add_device(config)
    
    # Initialize Game Sequence, passing the event queue
    config_path = file_service.get_game_json_path(game_name)
    game_sequence_instance = GameSequence(
        config_path=config_path,
        input_queue=input_event_queue,
        output_manager=output_manager_instance
    )

    # Start the Input and Output Managers in separate threads
    input_thread = Thread(target=input_manager_instance.start)
    input_thread.daemon = True
    input_thread.start()

    output_thread = Thread(target=output_manager_instance.start)
    output_thread.daemon = True
    output_thread.start()

    # Add a short delay to allow threads to fully initialize
    # time.sleep(0.5)

    print("Starting game loop...")
    try:
        game_sequence_instance.run_sequence()
    except KeyboardInterrupt:
        print("Exiting...")
    finally:
        input_manager_instance.stop()
        output_manager_instance.stop()
        print("Exited.")

if __name__ == "__main__":
    main()