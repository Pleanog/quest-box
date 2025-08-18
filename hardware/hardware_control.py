# hardware_control.py
from gpiozero import Button

blue_button = Button(17)  # GPIO pin 17

def wait_for_press(button):
    print("Waiting for button press...")
    button.wait_for_press()
    print("Button was pressed!")