import os
import requests
from dotenv import load_dotenv
import colorama
from colorama import Fore, Style

# Initialize colorama for cross-platform colored output
colorama.init(autoreset=True)

# Define base directories
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_PATH = os.path.join(BASE_DIR, '.env')

# Load environment variables
load_dotenv(dotenv_path=ENV_PATH)

class AudioService:
    def __init__(self, default_voice_id="2EiwWnXFnvU5JabPnv8n"):
        self.api_key = os.getenv("ELEVEN_API_KEY")
        self.default_voice_id = default_voice_id

        if not self.api_key:
            print(f"{Fore.RED}Error: ELEVEN_API_KEY not found in .env file.{Style.RESET_ALL}")
    
    def _create_game_directory(self, game_name):
        """Creates the game-specific audio directory if it doesn't exist."""
        game_audio_dir = os.path.join(BASE_DIR, 'game', game_name)
        if not os.path.exists(game_audio_dir):
            print(f"{Fore.YELLOW}Creating game audio directory: {game_audio_dir}{Style.RESET_ALL}")
            os.makedirs(game_audio_dir)
        return game_audio_dir

    def generate_and_save_audio(self, text, file_name, game_name, voice_id=None):
        """
        Generates audio from text and saves it to a game-specific directory.

        Args:
            text (str): The text to be converted to speech.
            file_name (str): The name for the audio file (e.g., 'intro.mp3').
            game_name (str): The name of the game for directory organization.
            voice_id (str, optional): The ElevenLabs voice ID. Defaults to the
                                      service's default voice.
        Returns:
            str: The full path to the saved audio file, or None if failed.
        """
        if not self.api_key:
            return None

        voice_id = voice_id if voice_id else self.default_voice_id

        print(f"{Fore.CYAN}Connecting to ElevenLabs API for '{game_name}'...{Style.RESET_ALL}")
        
        api_url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
        headers = {
            "Content-Type": "application/json",
            "xi-api-key": self.api_key
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
    service = AudioService()
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