# game_audio_generator.py

import os
import json
from colorama import Fore, Style
from elevenlabsAPI.tts_service import TTSService
from filename_service import FileNameService

# colorama.init(autoreset=True)

class GameAudioGenerator:
    """Generates and saves all required audio files for a new game configuration."""

    def __init__(self, base_dir: str, audio_service: TTSService):
        self.file_service = FileNameService(base_dir)
        self.audio_service = audio_service

    def generate_all_game_audio(self, game_name: str) -> bool:
        """
        Reads the game JSON and generates audio for all narrative text fields.
        
        Args:
            game_name (str): The file-safe name of the game (e.g., 'the-sheriffs-safe').
            
        Returns:
            bool: True if audio generation completed without critical errors.
        """
        game_json_path = self.file_service.get_game_json_path(game_name)
        audio_folder_path = self.file_service.get_audio_folder_path(game_name)
        
        print(f"{Fore.BLUE}--- Starting Audio Generation for {game_name} ---{Style.RESET_ALL}")
        
        # 1. Load the Game JSON
        try:
            with open(game_json_path, 'r', encoding='utf-8') as f:
                game_data = json.load(f)
        except FileNotFoundError:
            print(f"{Fore.RED}Error: Game JSON not found at {game_json_path}.{Style.RESET_ALL}")
            return False
        except json.JSONDecodeError:
            print(f"{Fore.RED}Error: Failed to decode Game JSON.{Style.RESET_ALL}")
            return False

        # 2. Ensure the audio directory exists
        if not os.path.exists(audio_folder_path):
            os.makedirs(audio_folder_path)

        # 3. Generate Audio for the Starting Description
        self._process_text_field(
            text=game_data.get("starting_description"),
            type_prefix="starting_description",
            path_name=game_name,
            game_name=game_name
        )

        # 4. Generate Audio for all Paths
        for path in game_data.get("paths", []):
            path_name = path.get("path_name", "unknown_path")
            
            self._process_text_field(
                text=path.get("description"),
                type_prefix="description",
                path_name=path_name,
                game_name=game_name
            )
            
            self._process_text_field(
                text=path.get("hint"),
                type_prefix="hint",
                path_name=path_name,
                game_name=game_name
            )
            
            self._process_text_field(
                text=path.get("death_text"),
                type_prefix="death_text",
                path_name=path_name,
                game_name=game_name
            )

        print(f"{Fore.BLUE}--- Audio Generation Complete ---{Style.RESET_ALL}")
        return True

    def _process_text_field(self, text: str, type_prefix: str, path_name: str, game_name: str):
        """Helper method to generate audio for a single text field."""
        if not text:
            print(f"{Fore.YELLOW}Warning: Skipping empty text for {type_prefix} in {path_name}.{Style.RESET_ALL}")
            return

        file_name = self.file_service.get_audio_filename(type_prefix, path_name)
        
        # The AudioService is assumed to handle the API call and file saving.
        saved_path = self.audio_service.generate_and_save_audio(
            text=text,
            file_name=file_name,
            game_name=game_name # This is the key that tells the AudioService where to save
        )
        if not saved_path:
            print(f"{Fore.RED}Failed to generate audio for: {file_name}{Style.RESET_ALL}")