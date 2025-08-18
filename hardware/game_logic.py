# game_logic.py
def play_room(room_data, trigger_map):
    print(room_data["description"])
    
    input_sequence = []
    
    for expected_trigger in room_data["solution_sequence"]:
        print(f"Waiting for: {expected_trigger}")
        btn = trigger_map[expected_trigger]
        btn.wait_for_press()
        print(f"{expected_trigger} pressed!")
        input_sequence.append(expected_trigger)
    
    if input_sequence == room_data["solution_sequence"]:
        print("Room completed successfully!")
        # run on_success commands
        return True
    else:
        print(room_data["death_text"])
        # run on_failure commands
        return False