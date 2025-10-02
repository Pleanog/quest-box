# # sound_controller.py

# import pygame
# import os
# import time
# from colorama import Fore, Style
# from pathlib import Path
# from filename_service import FileNameService 

# class SoundController:
#     def __init__(self, file_service):
#         self.file_service = file_service
#         self.device_name = "plughw:8,0" # Define your audio device here
#         self._is_initialized = False
        
#         # Initialize the mixer specifically. 
#         # pygame.init() must have been called beforehand.
#         try:
#             pygame.mixer.init(frequency=44100, devicename=self.device_name)
#             self._is_initialized = True
#             print(f"SoundController: Pygame mixer initialized successfully on {self.device_name}.")
#         except pygame.error as e:
#             print(f"SoundController Error: Failed to initialize mixer: {e}")
#             self._is_initialized = False

#     def set_effect(self, type_prefix: str, path_name: str, game_name: str, loop: bool = False):
#         if not self._is_initialized:
#             print("SoundController: Mixer not initialized, skipping playback.")
#             return

#         # 1. Logic to get the file path (using self.file_service)
#         try:
#             file_name = self.file_service.get_audio_filename(type_prefix, path_name)
#             folder = self.file_service.get_audio_folder_path(game_name)
#             path = Path(folder) / file_name
            
#             if not path.exists():
#                 print(f"SoundController Error: File not found: {path}")
#                 return

#             # 2. Play the sound (actual Pygame calls)
#             # -1 for infinite loop, 0 for once
#             pygame.mixer.music.stop()
#             pygame.mixer.music.load(str(path))
#             pygame.mixer.music.play(-1 if loop else 0)
#             print(f"SoundController: Playing {path.name} (Loop: {loop})")
#         except Exception as e:
#             print(f"SoundController Playback Error: {e}")

#     # Add a stop/cleanup method for the output manager to use
#     def stop(self):
#         if self._is_initialized:
#             pygame.mixer.music.stop()
#             # Note: pygame.quit() is handled by main.py
#             print("SoundController: Music stopped.")
            
#             # # sound_controller.py

# # import pygame
# # import os
# # import time
# # from colorama import Fore, Style
# # from pathlib import Path
# # from filename_service import FileNameService 

# # try:
# #     pygame.mixer.init()
# # except Exception as e:
# #     print(f"{Fore.RED}FATAL ERROR: Could not initialize Pygame Mixer: {e}. Sound will not work.{Style.RESET_ALL}")


# # class SoundController:
# #     """
# #     Controller for playing audio files using pygame.mixer.
# #     It is designed to be run from the OutputManager's worker thread.
# #     """
# #     def __init__(self, file_service: FileNameService):
# #         self.file_service = file_service
# #         # Check if the mixer is ready
# #         if not pygame.mixer.get_init():
# #             print(f"{Fore.RED}SoundController initialized but Pygame Mixer is NOT running.{Style.RESET_ALL}")
        
# #     def start(self):
# #         """Placeholder for consistency with other controllers. Mixer is already running."""
# #         print(f"{Style.DIM}SoundController is ready.{Style.RESET_ALL}")

# #     def stop(self):
# #         """Stops any currently playing music."""
# #         pygame.mixer.music.stop()
# #         print(f"{Fore.RED}SoundController stopped.{Style.RESET_ALL}")
    
# #     # sound_controller.py

# #     def set_effect(self, type_prefix: str, path_name: str, game_name: str, loop: bool = False, **kwargs):
# #         """
# #         Plays the audio file by using the FileNameService to build the path.
# #         """
# #         # --- DEBUG: Show what was received ---
# #         print(f"{Fore.CYAN}--- SoundController: Received command ---{Style.RESET_ALL}")
# #         print(f"{Fore.CYAN}  - type_prefix: {type_prefix}{Style.RESET_ALL}")
# #         print(f"{Fore.CYAN}  - path_name:   {path_name}{Style.RESET_ALL}")
# #         print(f"{Fore.CYAN}  - game_name:   {game_name}{Style.RESET_ALL}")
# #         # --- END DEBUG ---

# #         audio_file_name = self.file_service.get_audio_filename(type_prefix, path_name)
# #         audio_folder = self.file_service.get_audio_folder_path(game_name)
# #         full_path = Path(os.path.join(audio_folder, audio_file_name))
        
# #         file_path_object = full_path.resolve()

# #         # --- DEBUG: Show the calculated path ---
# #         print(f"{Fore.CYAN}  - Calculated Filename: {audio_file_name}{Style.RESET_ALL}")
# #         print(f"{Fore.CYAN}  - Final Absolute Path: {file_path_object}{Style.RESET_ALL}")
# #         # --- END DEBUG ---
        
# #         if not file_path_object.exists():
# #             print(f"{Fore.RED}Sound Error: File not found at path: {file_path_object}{Style.RESET_ALL}")
# #             return
        
# #         if not pygame.mixer.get_init():
# #             print(f"{Fore.RED}Sound Error: Pygame Mixer is not initialized.{Style.RESET_ALL}")
# #             return
            
# #         try:
# #             pygame.mixer.music.stop()
# #             pygame.mixer.music.load(str(file_path_object))
# #             print(f"{Fore.CYAN}  - Pygame: File loaded successfully.{Style.RESET_ALL}") # <-- DEBUG
            
# #             loop_count = -1 if loop else 0 
# #             pygame.mixer.music.play(loop_count)
# #             print(f"{Fore.GREEN}🔊 Playing sound: {file_path_object.name}{Style.RESET_ALL}") # <-- DEBUG

# #         except pygame.error as e:
# #             print(f"{Fore.RED}Pygame Playback Error: {e} for file {file_path_object}{Style.RESET_ALL}")
# #         except Exception as e:
# #             print(f"{Fore.RED}Unexpected Sound Error: {e}{Style.RESET_ALL}")

# # if __name__ == "__main__":
# #     print(f"{Fore.YELLOW}--- SoundController Test Started ---{Style.RESET_ALL}")

# #     # --- Configuration ---
# #     BASE_DIR = Path(__file__).parent.parent
# #     TEST_GAME_NAME = "the-curse-of-the-krakens-chest"
# #     TEST_PATH_NAME = "the_siren's_song"
# #     TEST_TYPE = "description"
    
# #     # --- Dependencies ---
# #     # This is a simple "mock" of your service for testing purposes.
# #     # This ensures the test can run even without the full FileNameService implementation.
# #     class MockFileNameService:
# #         def __init__(self, base_dir):
# #             self.base_dir = Path(base_dir)
# #         def get_audio_filename(self, type_prefix, path_name):
# #             # Simplified version of your service's logic
# #             # clean_path = path_name.replace("'", "").replace(" ", "_")
# #             return f"{type_prefix}_{path_name}.mp3"
# #         def get_audio_folder_path(self, game_name):
# #             return str(self.base_dir / "games" / game_name / "audio")

# #     file_service = MockFileNameService(str(BASE_DIR))

# #     # --- Pre-Test File Check ---
# #     TEST_FILENAME = file_service.get_audio_filename(TEST_TYPE, TEST_PATH_NAME)
# #     TEST_AUDIO_PATH = Path(file_service.get_audio_folder_path(TEST_GAME_NAME)) / TEST_FILENAME

# #     if not TEST_AUDIO_PATH.exists():
# #         print(f"{Fore.RED}FATAL TEST ERROR: Test audio file not found!{Style.RESET_ALL}")
# #         print(f"Please ensure a file exists at path: {TEST_AUDIO_PATH.resolve()}{Style.RESET_ALL}")
# #     else:
# #         # Initialize Controller
# #         controller = SoundController(file_service=file_service)
        
# #         # --- Test 1: Single Playback (Blocking) ---
# #         print("\n--- Test 1: Single Playback (Waiting for finish) ---")
# #         controller.set_effect(
# #             type_prefix=TEST_TYPE,
# #             path_name=TEST_PATH_NAME,
# #             game_name=TEST_GAME_NAME,
# #             loop=False
# #         )
        
# #         # IMPROVEMENT: Wait intelligently until the sound is done.
# #         print("Waiting for sound to finish...")
# #         while pygame.mixer.music.get_busy():
# #             time.sleep(0.1) # Check every 100ms
# #         print("Sound has finished playing.")

# #         # --- Test 2: Looping Playback (Stop after 3 seconds) ---
# #         print("\n--- Test 2: Looping Playback (Stopping manually) ---")
# #         controller.set_effect(
# #             type_prefix=TEST_TYPE,
# #             path_name=TEST_PATH_NAME,
# #             game_name=TEST_GAME_NAME,
# #             loop=True
# #         )
        
# #         print("Waiting 3 seconds while looping...")
# #         time.sleep(3) 
# #         controller.stop()
# #         print("Looping sound stopped.")
        
# #     print(f"\n{Fore.YELLOW}--- SoundController Test Finished ---{Style.RESET_ALL}")

# #     # THE MOST IMPORTANT FIX: Cleanly shut down Pygame and release the audio device.
# #     print("Shutting down Pygame mixer...")
# #     pygame.quit()