# tts_service.py
 
import os
import requests
from dotenv import load_dotenv
import colorama
from colorama import Fore, Style
from elevenlabs_client import ElevenLabsClient
from hardware.filename_service import FileNameService 

colorama.init(autoreset=True)

# Load environment variables
load_dotenv(dotenv_path=ENV_PATH)
class TTSService: # Renamed from AudioService for clarity
    def __init__(self, base_dir: str, default_voice_id="2EiwWnXFnvU5JabPnv8n"):
        self.eleven_client = ElevenLabsClient()
        self.file_service = FileNameService(base_dir) # <--- Use the central file service
        self.default_voice_id = default_voice_id
    
    def generate_and_save_audio(self, text, file_name, game_name, voice_id=None):
        if not self.eleven_client.is_ready():
            return None

        voice_id = voice_id if voice_id else self.default_voice_id

        # --- Use file_service for path creation ---
        # The new audio folder path: games/gamename/audio
        game_audio_dir = self.file_service.get_audio_folder_path(game_name)
        file_path = os.path.join(game_audio_dir, file_name)

        # 1. Ensure audio directory exists
        if not os.path.exists(game_audio_dir):
             os.makedirs(game_audio_dir) # Create folder via os, but use service path

        print(f"{Fore.CYAN}Connecting to ElevenLabs API for TTS: '{game_name}'...{Style.RESET_ALL}")
        
        # Use the official client's methods or stick to direct requests if preferred
        api_url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
        headers = {
             "Content-Type": "application/json",
             "xi-api-key": self.eleven_client.api_key # Use the shared key
        }
        data = {
             "text": text,
             "model_id": "eleven_multilingual_v2"
        }

        try:
            response = requests.post(api_url, json=data, headers=headers)
            response.raise_for_status()
            print(f"{Fore.GREEN}Successfully received audio stream.{Style.RESET_ALL}")
            audio_data = response.content
        except requests.exceptions.HTTPError as err:
            print(f"{Fore.RED}HTTP Error: {err}{Style.RESET_ALL}")
            return None
        except requests.exceptions.RequestException as err:
            print(f"{Fore.RED}Request Error: {err}{Style.RESET_ALL}")
            return None

        # Save audio to the specified game directory
        game_audio_dir = self._create_game_directory(game_name)
        file_path = os.path.join(game_audio_dir, file_name)

        print(f"{Fore.CYAN}Saving audio to: {file_path}{Style.RESET_ALL}")
        with open(file_path, 'wb') as f:
            f.write(audio_data)
        print(f"{Fore.GREEN}Audio saved successfully.{Style.RESET_ALL}")
        return file_path

if __name__ == "__main__":
    # Example Usage for testing
    service = TTSService()
    test_sentence = "Hello, this is a test from the audio service."
    test_game_name = "test-game"
    test_file_name = "test_intro.mp3"

    print(f"{Fore.BLUE}--- Running Audio Service Test ---{Style.RESET_ALL}")
    
    saved_path = service.generate_and_save_audio(
        text=test_sentence,
        file_name=test_file_name,
        game_name=test_game_name
    )

    if saved_path:
        print(f"{Fore.GREEN}Audio file saved at: {saved_path}{Style.RESET_ALL}")
    else:
        print(f"{Fore.RED}Audio generation failed.{Style.RESET_ALL}")