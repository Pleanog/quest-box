# main.py (Updated)

# # ! ---------------------------
# # ! Needs to run with sudo !!!!
# # ! because of led controller !
# # ! ---------------------------

import sys
import os
import time
from pathlib import Path
from threading import Thread
from queue import Queue

# Append parent directory to sys.path to resolve local imports (as per your original setup)
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

# Import shared service setup (assuming your elevenlabsAPI folder/files are correctly named)
from geminiAPI.gemini_client import generate_room_configuration
from elevenlabsAPI.tts_service import TTSService # Use TTSService for audio_service
from game_audio_generator import GameAudioGenerator
from filename_service import FileNameService

# Import Core Game Components
from game_sequence import GameSequence
from input_manager import InputManager
from output_manager import OutputManager
from led_controller import LEDController
from vibration_motor_controller import VibrationController
from bus_manager import I2C_BUS_LOCK

# Import the new Menu Manager
from menu_manager import MenuManager 

BASE_DIR = Path(__file__).parent.parent


def main():
    # --- 1. INITIALIZE THREAD MANAGERS (needed for menu input/output) ---
    print("--- 1. Initializing System Components ---")
    
    # Queues for inter-thread communication
    input_event_queue = Queue()
    output_command_queue = Queue()

    # Initialize Controllers
    led_controller = LEDController()
    vibration_controller = VibrationController()
    
    # Initialize Services
    file_service = FileNameService(str(BASE_DIR))
    audio_service = TTSService(str(BASE_DIR)) # TTS for menu audio

    # Add controllers to the OutputManager
    output_manager_instance = OutputManager(output_command_queue)
    output_manager_instance.add_controller("light", led_controller)
    output_manager_instance.add_controller("vibration", vibration_controller)
    output_manager_instance.add_controller("tts_service", audio_service)

    # Define device configurations (Hint and Repeat are crucial here)
    device_configs = [
        {"type": "sx1509_button", "value": "red", "pin": 2},
        {"type": "sx1509_button", "value": "blue", "pin": 12},
        {"type": "sx1509_button", "value": "yellow", "pin": 4},
        {"type": "sx1509_button", "value": "green", "pin": 5},
        {"type": "sx1509_button", "value": "hint", "pin": 13},     # MENU/HINT
        {"type": "sx1509_button", "value": "repeat", "pin": 6},   # MENU/REPEAT
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
        game_name=game_name
    )

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
    
    
# # # ! ---------------------------
# # # ! Needs to run with sudo !!!!
# # # ! because of led controller !
# # # ! ---------------------------

# # main.py

# import sys
# import os
# import time
# from pathlib import Path
# from threading import Thread
# from queue import Queue

# from game_sequence import GameSequence
# from input_manager import InputManager
# from output_manager import OutputManager
# from led_controller import LEDController
# from vibration_motor_controller import VibrationController
# from bus_manager import I2C_BUS_LOCK

# from geminiAPI.gemini_client import generate_room_configuration
# from elevenlabsAPI.tts_service import TTSService
# from game_audio_generator import GameAudioGenerator
# from filename_service import FileNameService

# from menu_manager import MenuManager 

# current_dir = os.path.dirname(os.path.abspath(__file__))
# parent_dir = os.path.dirname(current_dir)
# sys.path.append(parent_dir)
# BASE_DIR = Path(__file__).parent.parent

# def main():

#     # Gemini: here i would like to have a menu to select between different game
#     # first of all there are to buttons called hint and repeat.
#     # Initially i want to play a sound that explains the menu for now printing it into the console i sufficient.
#     # "Welcome to questbox, player - play alone or with a friend - emegre into a new game world every time - solve puzzles - find clues - and find solution before time runs out OR DIE."
#     # 'You can select a game by pressing the slect game button - to start the game press the start button - during the game you can get a hint by pressing the hint button - to repeat the last spoken text press the repeat button'
#     # To generate a new game, direclty press the start game button.
#     # Pressing the hint button initialy switches between the offline saved games in the games folder. there i would have a list of games that are stored offline that can be found in the games/aviable_games.txt
#     # once the game is selected, pressing the repeat button starts the game. during the game, pressing the hint button gives a hint for the current puzzle, pressing the repeat button repeats the last spoken text.
#     # So the user hase the option to let gemini generate a new game by starting instantly or select an offline saved game by selecting a game using the hint / switch button.
#     # each game is stored in a folder with the name of the game and contains the game.json and the audio files.
#     # switching works by just reading the next line in the games/aviable_games.txt file and printing the name into the console, pressing play after an initial switching starts the selected game
#     # After the user switched through all games in the aviable_games.txt file, it lets the user again start a new game generated by gemini. or by swicthing again the user again switches through the aviable games.
#     # once the game is started, the game.json is loaded and the game starts.
#     # once the game is finished, the user is again in the menu and can select a new game or start a new generated game
#     # for now i just want to generate a new game and start it directly help me make this menu into a seperat class or function that is called in the main function before starting the game sequence.

#     # --- 1. GAME GENERATION AND AUDIO PREP ---
#     print("--- 1. Initializing Game Generation ---")
    
#     # 1. Call Gemini API to generate the game JSON
#     # This returns the file-safe name (e.g., 'the-krakens-cache')
#     # game_name = generate_room_configuration()

#     game_name = "the-curse-of-the-krakens-chest"
    
#     if not game_name:
#         print("FATAL ERROR: Failed to generate a new room configuration. Exiting.")
#         return

#     # 2. Initialize Services needed for Audio Generation/Playback
#     file_service = FileNameService(str(BASE_DIR))
#     audio_service = TTSService(str(BASE_DIR))
    
#     # 3. Generate all audio files for the new game
#     audio_generator = GameAudioGenerator(str(BASE_DIR), audio_service)
#     audio_success = audio_generator.generate_all_game_audio(game_name)
    
#     if not audio_success:
#         print("Warning: Some audio files failed to generate. Continuing with available files.")
        
#     # --- 2. START GAME THREADS ---
#     print("--- 2. Starting Game System ---")

#     # Queues for inter-thread communication
#     input_event_queue = Queue()
#     output_command_queue = Queue()

#     # Initialize Controllers
#     led_controller = LEDController()
#     vibration_controller = VibrationController()

#     # Add controllers to the OutputManager
#     output_manager_instance = OutputManager(output_command_queue)
#     output_manager_instance.add_controller("light", led_controller)
#     output_manager_instance.add_controller("vibration", vibration_controller)
#     output_manager_instance.add_controller("tts_service", audio_service)
#     # output_manager_instance.add_controller("sound", sound_controller)

#     # Define device configurations
#     device_configs = [
#         {"type": "sx1509_button", "value": "red", "pin": 2},
#         {"type": "sx1509_button", "value": "blue", "pin": 12},
#         {"type": "sx1509_button", "value": "yellow", "pin": 4},
#         {"type": "sx1509_button", "value": "green", "pin": 5},
#         {"type": "sx1509_button", "value": "hint", "pin": 13},
#         {"type": "sx1509_button", "value": "repeat", "pin": 6},
#         {"type": "gyro", "value": "shaking"},
#         {"type": "rotary_encoder", "name": "rotary_encoder_picture", "clk_pin": 20, "dt_pin": 21, "button_pin": 16},
#         {"type": "rotary_encoder", "name": "rotary_encoder_number", "clk_pin": 13, "dt_pin": 19, "button_pin": 26},
#         {"type": "distance_sensor", "trigger_pin": 23, "echo_pin": 24},
#     ]

#     # Initialize Managers, passing the necessary queues
#     # input_manager_instance = InputManager(input_event_queue)
#     input_manager_instance = InputManager(input_event_queue, bus_lock=I2C_BUS_LOCK, device_configs=device_configs)

#     # Add devices to the Input Manager
#     for config in device_configs:
#         input_manager_instance.add_device(config)
    
#     # Initialize Game Sequence, passing the event queue
#     config_path = file_service.get_game_json_path(game_name)
#     game_sequence_instance = GameSequence(
#         config_path=config_path,
#         input_queue=input_event_queue,
#         output_manager=output_manager_instance
#     )

#     # Start the Input and Output Managers in separate threads
#     input_thread = Thread(target=input_manager_instance.start)
#     input_thread.daemon = True
#     input_thread.start()

#     output_thread = Thread(target=output_manager_instance.start)
#     output_thread.daemon = True
#     output_thread.start()

#     # Add a short delay to allow threads to fully initialize
#     # time.sleep(0.5)

#     print("Starting game loop...")
#     try:
#         game_sequence_instance.run_sequence()
#     except KeyboardInterrupt:
#         print("Exiting...")
#     finally:
#         input_manager_instance.stop()
#         output_manager_instance.stop()
#         print("Exited.")

# if __name__ == "__main__":
#     main()