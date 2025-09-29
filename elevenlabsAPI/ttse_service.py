# ttse_service.py (Fully Updated)

import os
import colorama
# Note: We need to import load_dotenv, ElevenLabs, and requests if using them directly, 
# but we will rely on elevenlabs_client to handle the setup/key/client object.
from dotenv import load_dotenv # Needed for initialization if not handled in elevenlabs_client
from elevenlabsAPI.elevenlabs_manager import ElevenLabsClient
import requests # Needed to catch specific HTTP exceptions if the elevenlabs library doesn't handle them
from colorama import Fore, Style

# Initialize colorama
colorama.init(autoreset=True)

# --- IMPORTS FOR MODULARITY ---
# Assuming these modules are accessible in your environment
from elevenlabsAPI.elevenlabs_manager import ElevenLabsClient 
from filename_service import FileNameService 
# ------------------------------

# Define base directories and load environment variables
# Note: These lines are typically now handled within the ElevenLabsClient setup 
# to keep this file cleaner, but we keep the BASE_DIR definition to pass it to FileNameService.
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv() # Ensure .env is loaded

class TTSEService:
    def __init__(self):
        # 1. Initialize the shared API client
        self.eleven_client_wrapper = ElevenLabsClient()
        
        # 2. Get the actual ElevenLabs client instance
        self.elevenlabs = self.eleven_client_wrapper.client 
        
        # 3. Initialize the shared file service
        self.file_service = FileNameService(BASE_DIR) 
        
        # Check if the client is ready
        if not self.eleven_client_wrapper.is_ready():
            print(f"{Fore.RED}Warning: TTSE service disabled due to missing API key.{Style.RESET_ALL}")

    # --- REMOVE _create_sound_effects_directory METHOD ---
    # The responsibility for creating paths now belongs to FileNameService, 
    # and the directory creation is integrated into the generation method.
    
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
        # 1. Check if the ElevenLabs client is initialized
        if not self.elevenlabs:
            return None
        
        # 2. Build the full file path using the centralized service
        game_folder_path = self.file_service.get_game_folder_path(game_name)
        sound_effects_dir = os.path.join(game_folder_path, 'sound_effects')
        file_path = os.path.join(sound_effects_dir, file_name)

        # 3. Ensure sound effects directory exists
        if not os.path.exists(sound_effects_dir):
            print(f"{Fore.YELLOW}Creating sound effects directory: {sound_effects_dir}{Style.RESET_ALL}")
            os.makedirs(sound_effects_dir)

        # 4. Check if the file already exists (caching)
        if os.path.exists(file_path):
            print(f"{Fore.GREEN}Sound effect '{file_name}' already exists. Using cached file.{Style.RESET_ALL}")
            return file_path

        print(f"{Fore.CYAN}Connecting to ElevenLabs API for sound effect: '{prompt}'...{Style.RESET_ALL}")
        
        try:
            # Call the ElevenLabs API using the client instance
            audio_stream = self.elevenlabs.text_to_sound_effects.convert(text=prompt)
            print(f"{Fore.GREEN}Successfully received audio stream for sound effect.{Style.RESET_ALL}")
            
            # 5. Save the streamed audio data
            with open(file_path, 'wb') as f:
                # The returned object from convert is a generator/iterable stream
                for chunk in audio_stream:
                    if chunk:
                        f.write(chunk)
                        
            print(f"{Fore.GREEN}Sound effect saved successfully: {file_path}{Style.RESET_ALL}")
            return file_path
            
        # Catch specific requests exceptions if the library throws them, or just a general one
        except requests.exceptions.HTTPError as err:
            print(f"{Fore.RED}HTTP Error: {err}{Style.RESET_ALL}")
            return None
        except Exception as e:
            print(f"{Fore.RED}An unexpected error occurred during API call or saving: {e}{Style.RESET_ALL}")
            return None
            
if __name__ == "__main__":
    # Example Usage for testing
    service = TTSEService()
    
    print(f"{Fore.BLUE}--- Running TTSE Service Test ---{Style.RESET_ALL}")
    
    # Test a new sound effect
    test_sentence = "A large iron key turning in an old lock."
    test_game_name = "test-game"
    test_file_name = "test_key_lock.mp3"

    saved_path = service.generate_and_save_sound_effect(
        prompt=test_sentence,
        file_name=test_file_name,
        game_name=test_game_name
    )
    if saved_path:
        print(f"{Fore.GREEN}Audio file saved at: {saved_path}{Style.RESET_ALL}")