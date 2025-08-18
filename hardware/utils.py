# utils.py
import json
import pygame

def load_game_config(path='../gemini-api/rooms.json'):
    with open(path, 'r') as file:
        return json.load(file)
    

def play_audio(path):
    pygame.mixer.init()
    pygame.mixer.music.load(path)
    pygame.mixer.music.play()