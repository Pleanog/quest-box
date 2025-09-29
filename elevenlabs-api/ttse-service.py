# ttse-service.py

import os
from dotenv import load_dotenv
import requests
from elevenlabs.client import ElevenLabs
import colorama
from colorama import Fore, Style
import hashlib

# Initialize colorama
colorama.init(autoreset=True)

# Define base directories
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_PATH = os.path.join(BASE_DIR, '.env')

# Load environment variables
load_dotenv(dotenv_path=ENV_PATH)

class TTSEService:
    def __init__(self):
        self.api_key = os.getenv("ELEVEN_API_KEY")
        if not self.api_key:
            print(f"{Fore.RED}Error: ELEVEN_API_KEY not found in .env file.{Style.RESET_ALL}")
        
        # Initialize the ElevenLabs client
        self.elevenlabs = ElevenLabs(api_key=self.api_key)

    def _create_sound_effects_directory(self, game_name):
        """Creates the sound effects directory for a specific game if it doesn't exist."""
        game_audio_dir = os.path.join(BASE_DIR, 'games', game_name, 'sound_effects')
        if not os.path.exists(game_audio_dir):
            print(f"{Fore.YELLOW}Creating sound effects directory: {game_audio_dir}{Style.RESET_ALL}")
            os.makedirs(game_audio_dir)
        return game_audio_dir
    
    def generate_and_save_sound_effect(self, prompt, file_name, game_name):
        """
        Generates a sound effect from a text prompt and saves it with a specified filename.

        Args:
            prompt (str): The text description of the sound effect.
            file_name (str): The desired filename for the audio file (e.g., 'door_slam.mp3').
            game_name (str): The name of the game for directory organization.

        Returns:
            str: The full path to the saved audio file, or None if failed.
        """
        if not self.api_key:
            return None
        
        # Build the file path using the provided file_name
        game_audio_dir = self._create_sound_effects_directory(game_name)
        file_path = os.path.join(game_audio_dir, file_name)

        # Check if the file already exists (caching)
        if os.path.exists(file_path):
            print(f"{Fore.GREEN}Sound effect '{file_name}' already exists. Using cached file.{Style.RESET_ALL}")
            return file_path

        print(f"{Fore.CYAN}Connecting to ElevenLabs API for sound effect: '{prompt}'...{Style.RESET_ALL}")
        
        try:
            audio_stream = self.elevenlabs.text_to_sound_effects.convert(text=prompt)
            print(f"{Fore.GREEN}Successfully received audio stream for sound effect.{Style.RESET_ALL}")
            
            with open(file_path, 'wb') as f:
                for chunk in audio_stream:
                    if chunk:
                        f.write(chunk)
                        
            print(f"{Fore.GREEN}Sound effect saved successfully: {file_path}{Style.RESET_ALL}")
            return file_path
            
        except requests.exceptions.HTTPError as err:
            print(f"{Fore.RED}HTTP Error: {err}{Style.RESET_ALL}")
            return None
        except Exception as e:
            print(f"{Fore.RED}An error occurred: {e}{Style.RESET_ALL}")
            return None
        
if __name__ == "__main__":
    # Example Usage for testing
    service = TTSEService()
    
    print(f"{Fore.BLUE}--- Running TTSE Service Test ---{Style.RESET_ALL}")
    
    # Test a new sound effect
    test_sentence = "Sword being swung, then clashing with another blade, and a lound screaming battle cry afterwards"
    test_game_name = "test-game2"
    test_file_name = "test_sound_effect2.mp3"

    saved_path = service.generate_and_save_sound_effect(
        prompt=test_sentence,
        file_name=test_file_name,
        game_name=test_game_name
    )
    if saved_path:
        print(f"{Fore.GREEN}Audio file saved at: {saved_path}{Style.RESET_ALL}")
    
    # # Test the same sound effect to check caching
    # saved_path_cached = service.generate_and_save_sound_effect(
    #     prompt="A heavy dungeon door slams shut.",
    #     game_name=game_name
    # )
    # if saved_path_cached:
    #     print(f"{Fore.GREEN}Cached audio file path: {saved_path_cached}{Style.RESET_ALL}")