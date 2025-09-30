import subprocess
import pygame
import os
import time

pygame.mixer.init()

def play_sound(filename: str, loop: bool = False):
    """
    Plays a sound file from the 'audio' folder at the same level as the 'hardware' directory.
    
    Args:
        filename (str): Name of the mp3 file.
        loop (bool): If True, loops until stopped.
    """
    # pygame.mixer.init(frequency=44100)  # standard audio frequency
    file_path = os.path.join(os.path.dirname(__file__), "..", "audio", filename)
    file_path = os.path.abspath(file_path)

    print(f"Playing sound from path: {file_path}")

    file_path = "/home/philipp/quest-box/games/the-curse-of-the-krakens-chest/audio/description_the_siren's_song.mp3"

    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"Sound file not found: {file_path}")
    
    pygame.mixer.init(frequency=44100, devicename="plughw:8,0")
    pygame.mixer.music.load(file_path)
    pygame.mixer.music.play(-1 if loop else 0)


# from sounds import play_sound

def main():
    print("Starting sound test...")
    # Play the dessert sound once at the start
    play_sound("dessert-1.mp3", loop=False)
    # play_mp3("dessert-1.mp3", loop=False)
    while pygame.mixer.music.get_busy():
        time.sleep(1)
    # Your existing code...
    print("Game started!")

if __name__ == "__main__":
    main()
