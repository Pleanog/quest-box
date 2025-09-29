# elevenlabs_client.py

import os
from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs # Standard ElevenLabs client
from colorama import Fore, Style

# Load environment variables once for all services
load_dotenv()
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

class ElevenLabsClient:
    def __init__(self):
        self.api_key = os.getenv("ELEVEN_API_KEY")
        self.client = None
        
        if not self.api_key:
            print(f"{Fore.RED}Error: ELEVEN_API_KEY not found in .env file. Audio services disabled.{Style.RESET_ALL}")
        else:
            # Initialize the client from the official library
            self.client = ElevenLabs(api_key=self.api_key)

    def is_ready(self):
        return self.client is not None