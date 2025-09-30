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
            if input_event.value == self.HINT_BUTTON:
                # Cycle through options: Generate -> Game 1 -> Game 2 -> ... -> Generate
                self.current_selection_index = (self.current_selection_index + 1) % (len(self.available_games) + 1)
                if self.current_selection_index == len(self.available_games):
                    self.current_selection_index = -1 # Wrap back to Generate
                self.state_game_name = self._get_current_selection()
                self._print_menu_state()
                
            # Check for repeat/start button press
            elif input_event.value == self.REPEAT_BUTTON:
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