import pygame

# Initialize mixer
pygame.mixer.init()

# Load your MP3 file
pygame.mixer.music.load("/home/philipp/quest-box/audio/dessert-1.mp3")

# Play the file
pygame.mixer.music.play()


# Keep the program alive until the music finishes
while pygame.mixer.music.get_busy():
    pygame.time.Clock().tick(10)
