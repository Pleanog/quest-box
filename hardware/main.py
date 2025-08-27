# # ! ---------------------------
# # ! Needs to run with sudo !!!!
# # ! because of led controller !
# # ! ---------------------------

# main.py

from pathlib import Path
from threading import Thread
from queue import Queue
from game_sequence import GameSequence
from input_manager import InputManager
from output_manager import OutputManager
from led_controller import LEDController
from vibration_motor_controller import VibrationController
from bus_manager import I2C_BUS_LOCK

def main():
    # Queues for inter-thread communication
    input_event_queue = Queue()
    output_command_queue = Queue()

    # Initialize Controllers
    led_controller = LEDController()
    vibration_controller = VibrationController()

    # Define device configurations
    device_configs = [
        {"type": "sx1509_button", "value": "red", "pin": 2},
        {"type": "sx1509_button", "value": "blue", "pin": 12},
        {"type": "sx1509_button", "value": "yellow", "pin": 4},
        {"type": "sx1509_button", "value": "green", "pin": 5},
        {"type": "sx1509_button", "value": "black", "pin": 13},
        {"type": "gyro", "value": "shaking"},
        {"type": "rotary_encoder", "name": "image_dial", "clk_pin": 20, "dt_pin": 21, "button_pin": 16},
        {"type": "rotary_encoder", "name": "number_dial", "clk_pin": 13, "dt_pin": 19, "button_pin": 26},
        {"type": "distance_sensor", "trigger_pin": 23, "echo_pin": 24},
    ]

    # Initialize Managers, passing the necessary queues
    # input_manager_instance = InputManager(input_event_queue)
    input_manager_instance = InputManager(input_event_queue, bus_lock=I2C_BUS_LOCK, device_configs=device_configs)
    output_manager_instance = OutputManager(output_command_queue)

    # Add controllers to the OutputManager
    output_manager_instance.add_controller("light", led_controller)
    output_manager_instance.add_controller("vibration", vibration_controller)
    # output_manager_instance.add_controller("sound", sound_controller)


    # Add devices to the Input Manager
    for config in device_configs:
        input_manager_instance.add_device(config)
    
    # Initialize Game Sequence, passing the event queue
    script_dir = Path(__file__).parent
    config_path = script_dir.parent / "gemini-api" / "room-small.json"
    game_sequence_instance = GameSequence(
        config_path=config_path,
        input_queue=input_event_queue,
        output_manager=output_manager_instance
    )

    # Start the Input and Output Managers in separate threads
    input_thread = Thread(target=input_manager_instance.start)
    input_thread.daemon = True
    input_thread.start()

    output_thread = Thread(target=output_manager_instance.start)
    output_thread.daemon = True
    output_thread.start()

    # Add a short delay to allow threads to fully initialize
    # time.sleep(0.5)

    print("Starting game loop...")
    try:
        game_sequence_instance.run_sequence()
    except KeyboardInterrupt:
        print("Exiting...")
    finally:
        input_manager_instance.stop()
        output_manager_instance.stop()
        print("Exited.")

if __name__ == "__main__":
    main()