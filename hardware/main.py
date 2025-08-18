from utils import load_game_config, play_audio
from game_logic import play_room
from hardware_control import trigger_map

game_data = load_game_config()

print(game_data["starting_description"])

for room in game_data["paths"]:
    success = play_room(room, trigger_map)
    if not success:
        print("You have failed the dungeon!")
        break

print("Game Over")