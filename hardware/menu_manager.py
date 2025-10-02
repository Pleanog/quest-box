# menu_manager.py

import os
import time
from queue import Queue
from colorama import Fore, Style
from typing import Literal

from filename_service import FileNameService 

#colorama.init(autoreset=True)

class MenuManager:
    """Handles the initial game selection menu."""

    # Menu State constant
    GENERATE_NEW_GAME = "GENERATE_NEW_GAME"
    
    def __init__(self, input_queue: Queue, output_manager, file_service: FileNameService):
        self.input_queue = input_queue
        self.output_manager = output_manager
        self.file_service = file_service
        self.available_games = self._load_available_games()
        self.current_selection_index = -1  # -1 for "Generate New Game"
        self.HINT_BUTTON = "hint"
        self.REPEAT_BUTTON = "repeat"
        self.state_game_name: str | Literal['GENERATE_NEW_GAME'] = self.GENERATE_NEW_GAME

    def _load_available_games(self) -> list[str]:
        """Reads the available_games.txt file."""
        games_dir = self.file_service.get_game_folder_path("") # Gets the 'games' directory path
        available_games_file = os.path.join(games_dir, 'available_games.txt')
        
        games = []
        try:
            with open(available_games_file, 'r') as f:
                # Filter out empty lines and sanitize
                games = [line.strip().lower() for line in f if line.strip()]
        except FileNotFoundError:
            print(f"{Fore.YELLOW}Warning: 'available_games.txt' not found. Only 'Generate New Game' option available.{Style.RESET_ALL}")
        
        return games

    def _get_current_selection(self) -> str:
        """Returns the user's current game selection name."""
        if self.current_selection_index == -1:
            return self.GENERATE_NEW_GAME
        
        if 0 <= self.current_selection_index < len(self.available_games):
            return self.available_games[self.current_selection_index]
            
        # Should not happen, but reset if index is out of bounds
        self.current_selection_index = -1
        return self.GENERATE_NEW_GAME

    def _print_menu_state(self):
        """Prints the current menu state to the console."""
        selection = self._get_current_selection()
        
        print("\n" + "="*50)
        print(f"{Fore.BLUE}QUESTBOX MAIN MENU{Style.RESET_ALL}")
        print("="*50)
        
        # Display all options
        options = ["GENERATE NEW GAME"] + self.available_games
        for i, option in enumerate(options):
            prefix = f"{Fore.GREEN}>>{Style.RESET_ALL}" if (i - 1) == self.current_selection_index else "  "
            print(f"{prefix} {option}")
            
        print("-" * 50)
        print(f"{Fore.CYAN}Controls:{Style.RESET_ALL}")
        print(f"  {Fore.YELLOW}[{self.HINT_BUTTON.upper()}]{Style.RESET_ALL}: Switch/Select Next Game")
        print(f"  {Fore.YELLOW}[{self.REPEAT_BUTTON.upper()}]{Style.RESET_ALL}: Start Selected Game")
        print("-" * 50)

    def _play_intro_audio(self):
        intro_text = (
            "Welcome to QuestBox, player. Emerge into a new game world every time. "
            "You can select a game by pressing the hint button, or start the selected "
            "game by pressing the repeat button. To generate a brand new game, just press "
            "the repeat button instantly."
        )
        
        # Placeholder: Print to console and output to TTS manager for actual playback
        print(f"\n{Fore.MAGENTA}INTRO AUDIO (TTS Placeholder):{Style.RESET_ALL} {intro_text}")
        # In a real setup, you would call:
        # self.output_manager.send_command("tts_service", "play", text=intro_text)

    def run_menu(self) -> str | Literal['GENERATE_NEW_GAME']:
        """
        Runs the menu loop, returning the selected game name or the generation signal.
        For now, this is a placeholder that bypasses the loop and returns the generate signal.
        """
        self._play_intro_audio()
        
        # Set initial state to the first option: GENERATE_NEW_GAME
        self.current_selection_index = -1
        self._print_menu_state() 
        
        while True:
            try:
                input_event = self.input_queue.get_nowait() 
            except:
                time.sleep(0.1)
                continue
            
            # Check for hint/switch button press
            if input_event.value == self.REPEAT_BUTTON:
                # Cycle through options: Generate -> Game 1 -> Game 2 -> ... -> Generate
                self.current_selection_index = (self.current_selection_index + 1) % (len(self.available_games) + 1)
                if self.current_selection_index == len(self.available_games):
                    self.current_selection_index = -1 # Wrap back to Generate
                self.state_game_name = self._get_current_selection()
                self._print_menu_state()
                
            # Check for repeat/start button press
            elif input_event.value == self.HINT_BUTTON:
                self.state_game_name = self._get_current_selection()
                print(f"\n{Fore.GREEN}STARTING: {self.state_game_name}{Style.RESET_ALL}")
                return self.state_game_name
        
    
if __name__ == "__main__":
        # Simple test run
        from queue import Queue
        dummy_input_queue = Queue()
        dummy_output_manager = None
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        file_service = FileNameService(base_dir)
        
        menu = MenuManager(dummy_input_queue, dummy_output_manager, file_service)
        selected_game = menu.run_menu()
        print(f"Menu exited with selection: {selected_game}")

# # menu_manager.py

# import os
# import sys  # <-- Import sys to modify the path
# import time
# import pygame
# from queue import Queue
# from colorama import Fore, Style
# from typing import Literal

# current_dir = os.path.dirname(os.path.abspath(__file__))
# parent_dir = os.path.dirname(current_dir)
# sys.path.append(parent_dir)

# # This will be resolved by the path fix in the test block
# from filename_service import FileNameService
# from elevenlabsAPI.tts_service import TTSService

# class MenuManager:
#     """Handles the initial game selection menu using direct pygame audio."""

#     # Menu State constant
#     GENERATE_NEW_GAME = "GENERATE NEW GAME"
    
#     def __init__(self, input_queue: Queue, file_service: FileNameService, tts_service: TTSService):
#         self.input_queue = input_queue
#         self.file_service = file_service
#         self.tts_service = tts_service
#         self.available_games = self._load_available_games()
#         self.current_selection_index = -1  # -1 for "Generate New Game"
        
#         # Swapped to match user request: Hint switches, Repeat starts.
#         self.SWITCH_BUTTON = "hint"
#         self.START_BUTTON = "repeat"

#         # Ensure the directory for menu audio exists
#         self.menu_audio_dir = os.path.join(self.file_service.get_audio_folder_path(), 'menu_audio')
#         os.makedirs(self.menu_audio_dir, exist_ok=True)


#     def _load_available_games(self) -> list[str]:
#         """Reads the available_games.txt file."""
#         games_dir = self.file_service.get_game_folder_path("")
#         available_games_file = os.path.join(games_dir, 'available_games.txt')
        
#         games = []
#         try:
#             with open(available_games_file, 'r') as f:
#                 games = [line.strip() for line in f if line.strip()]
#         except FileNotFoundError:
#             print(f"{Fore.YELLOW}Warning: 'available_games.txt' not found. Only 'Generate New Game' option available.{Style.RESET_ALL}")
        
#         return games

#     def _get_current_selection_text(self) -> str:
#         """Returns the user's current game selection name as a readable string."""
#         if self.current_selection_index == -1:
#             return self.GENERATE_NEW_GAME
        
#         if 0 <= self.current_selection_index < len(self.available_games):
#             # Convert snake_case to Title Case for reading out loud
#             return self.available_games[self.current_selection_index].replace('_', ' ').title()
            
#         self.current_selection_index = -1
#         return self.GENERATE_NEW_GAME

#     def _print_menu_state(self):
#         """Prints the current menu state to the console."""
#         print("\n" + "="*50)
#         print(f"{Fore.BLUE}QUESTBOX MAIN MENU{Style.RESET_ALL}")
#         print("="*50)
        
#         # Display all options
#         options = [self.GENERATE_NEW_GAME] + [game.replace('_', ' ').title() for game in self.available_games]
#         for i, option in enumerate(options):
#             prefix = f"{Fore.GREEN}>>{Style.RESET_ALL}" if (i - 1) == self.current_selection_index else "  "
#             print(f"{prefix} {option}")
            
#         print("-" * 50)
#         print(f"{Fore.CYAN}Controls:{Style.RESET_ALL}")
#         print(f"  {Fore.YELLOW}[{self.SWITCH_BUTTON.upper()}]{Style.RESET_ALL}: Switch/Select Next Game")
#         print(f"  {Fore.YELLOW}[{self.START_BUTTON.upper()}]{Style.RESET_ALL}: Start Selected Game")
#         print("-" * 50)

#     def _play_audio(self, text_to_speak: str):
#         """Generates (if needed) and plays an audio file for the given text."""
#         # Stop any currently playing audio
#         if pygame.mixer.music.get_busy():
#             pygame.mixer.music.stop()

#         # Generate a safe filename for the audio
#         filename = self.file_service.sanitize_filename(text_to_speak) + ".mp3"
#         filepath = os.path.join(self.menu_audio_dir, filename)

#         # Generate the audio file if it doesn't exist
#         if not os.path.exists(filepath):
#             print(f"{Fore.CYAN}Generating audio for: '{text_to_speak}'...{Style.RESET_ALL}")
#             self.tts_service.generate_audio(text_to_speak, filepath)
        
#         # Play the audio file
#         try:
#             pygame.mixer.music.load(filepath)
#             pygame.mixer.music.play()
#             print(f"{Fore.MAGENTA}AUDIO PLAYING:{Style.RESET_ALL} {text_to_speak}")
#         except pygame.error as e:
#             print(f"{Fore.RED}Error playing audio file {filepath}: {e}{Style.RESET_ALL}")

#     def _play_intro_audio(self):
#         intro_text = (
#             "Welcome to Quest Box. Select a game by pressing the hint button, "
#             "then start the game by pressing the repeat button. "
#             "To generate a new game, press the repeat button now."
#         )
#         self._play_audio(intro_text)

#     def run_menu(self) -> str:
#         """Runs the menu loop, returning the selected game name or the generation signal."""
#         self._play_intro_audio()
        
#         self.current_selection_index = -1
#         self._print_menu_state() 
        
#         # Wait for intro audio to finish before accepting input
#         while pygame.mixer.music.get_busy():
#             time.sleep(0.1)
        
#         while True:
#             try:
#                 # Blocking get is better for a simple loop like this
#                 input_event = self.input_queue.get(timeout=0.1) 
#             except:
#                 continue
            
#             # Button to cycle through the options
#             if input_event.value == self.SWITCH_BUTTON:
#                 self.current_selection_index = (self.current_selection_index + 1) % (len(self.available_games) + 1)
#                 if self.current_selection_index == len(self.available_games):
#                     self.current_selection_index = -1 # Wrap back to Generate New Game
                
#                 selection_text = self._get_current_selection_text()
#                 self._print_menu_state()
#                 self._play_audio(selection_text) # Read the new selection out loud
                
#             # Button to confirm selection and start
#             elif input_event.value == self.START_BUTTON:
#                 if self.current_selection_index == -1:
#                     selection = self.GENERATE_NEW_GAME
#                 else:
#                     selection = self.available_games[self.current_selection_index]
                
#                 print(f"\n{Fore.GREEN}STARTING: {selection}{Style.RESET_ALL}")
#                 self._play_audio(f"Starting {self._get_current_selection_text()}")
                
#                 # Wait for the "Starting..." audio to finish before returning
#                 while pygame.mixer.music.get_busy():
#                     time.sleep(0.1)
                
#                 return selection


# # --- Standalone Test Block ---
# if __name__ == "__main__":
#     # --- FIX: Add parent directory to sys.path to resolve local imports ---
    
#     # --------------------------------------------------------------------

#     print("--- Running MenuManager Standalone Test ---")

#     # 1. Define a dummy InputEvent class for testing
#     class DummyInputEvent:
#         def __init__(self, value):
#             self.value = value
#         def __repr__(self):
#             return f"InputEvent(value='{self.value}')"

#     # 2. Setup dummy file structure for the test
#     # Use a 'test_base' directory to avoid cluttering the main project
#     test_base_dir = os.path.join(os.path.dirname(__file__), 'test_base')
#     test_games_dir = os.path.join(test_base_dir, 'games')
#     os.makedirs(test_games_dir, exist_ok=True)
    
#     # Create a dummy available_games.txt
#     available_games_path = os.path.join(test_games_dir, 'available_games.txt')
#     with open(available_games_path, 'w') as f:
#         f.write("haunted_mansion\n")
#         f.write("space_odyssey\n")

#     # 3. Initialize Pygame and required services
#     pygame.init()
#     pygame.mixer.init()

#     dummy_input_queue = Queue()
    
#     # We need real instances of these services for the test to work
#     file_service = FileNameService(test_base_dir) 
#     # Ensure your API key is available for TTSService (e.g., in an .env file)
#     try:
#         tts_service = TTSService(test_base_dir)
#     except Exception as e:
#         print(f"{Fore.RED}Failed to initialize TTSService: {e}")
#         print(f"{Fore.YELLOW}Please ensure your ElevenLabs API key is configured correctly.{Style.RESET_ALL}")
#         pygame.quit()
#         exit()

#     # 4. Create and run the menu manager
#     menu = MenuManager(dummy_input_queue, file_service, tts_service)

#     # 5. Simulate button presses and run the menu in a thread
#     def simulate_input(q):
#         print("\n--- Simulating User Input ---")
#         time.sleep(10) # Wait for intro audio
        
#         print("Simulating SWITCH press (-> Haunted Mansion)")
#         q.put(DummyInputEvent("hint"))
#         time.sleep(3)
        
#         print("Simulating SWITCH press (-> Space Odyssey)")
#         q.put(DummyInputEvent("hint"))
#         time.sleep(3)
        
#         print("Simulating START press")
#         q.put(DummyInputEvent("repeat"))
        
#     # Run the simulation in a separate thread
#     sim_thread = Thread(target=simulate_input, args=(dummy_input_queue,))
#     sim_thread.daemon = True
#     sim_thread.start()

#     # The run_menu() call will block until a selection is made
#     selected_game = menu.run_menu()
    
#     print("\n" + "="*50)
#     print(f"{Fore.GREEN}Menu exited with selection: {selected_game}{Style.RESET_ALL}")
#     print("="*50)

#     # 6. Clean up
#     pygame.quit()
#     # Optional: Clean up dummy files
#     # import shutil
#     # shutil.rmtree(test_base_dir)
#     print("--- Test Finished ---")

