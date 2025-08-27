# Quest-Box: An Interactive Dungeon Adventures in a Box

## 📖 Project Overview

Quest-Box is a prototype of an interactive puzzle box that combines physical hardware with a dynamic, AI-powered narrative. Developed as a university project at LMU, this system demonstrates the integration of an LLM that communicates with the Raspberry Pi got get acces to various sensors and actuators to create an immersive, story-driven game. Like an AI powered pen and paper / dungeon adventures on a physical hardware box! The core of the project lies in its ability to translate physical input from the user into meaningful events that progress a branching narrative, while providing rich feedback through lights, sound, and vibration.

## ⚙️ System Architecture

The project is built on a modular, multi-threaded architecture to ensure real-time responsiveness and scalability.

* **`main.py`**: The central orchestrator. It initializes all hardware managers and the game logic, starting them in dedicated threads. It acts as the command center, coordinating the flow of data between components.
* **`InputManager`**: This module manages all physical input devices, such as custom buttons, rotary encoders, and sensors. It continuously polls these devices and translates their state changes into standardized `InputEvent` objects, which are then placed into a shared queue.
* **`OutputManager`**: The counterpart to the input manager, this module handles all physical outputs like LEDs and vibration motors. It receives commands from the game logic via a queue and dispatches them to the appropriate hardware controllers.
* **`GameSequence`**: This is the heart of the game logic. It reads a solution sequence from a JSON configuration file and waits for a series of correct `InputEvent`s. It tracks the player's progress and manages the game's state, including retries and victory/failure conditions.
* **Hardware Controllers**: Individual classes (e.g., `LEDController`, `RotaryEncoderController`, `DistanceController`) encapsulate the low-level logic for each specific piece of hardware. This design makes it easy to add or swap out components.

## ⚡️ Hardware and Software Requirements

* **Hardware**:
    * Raspberry Pi 4B
    * SX1509 I/O Expander
    * TCA9548A I2C Multiplexer (optional but recommended for multiple I2C devices)
    * GY-521 MPU6050 Gyroscope/Accelerometer
    * HC-SR04 Ultrasonic Distance Sensor
    * Rotary Encoders (with push-buttons)
    * Custom buttons, LEDs, and a vibration motor
* **Software**:
    * Raspberry Pi OS
    * Python 3.11+
    * `RPi.GPIO` library
    * `smbus` library (for I2C communication)
    * `colorama` (for colored console output)
    * `json`

## 🔌 Connecting to the Quest-Box

To connect to the Raspberry Pi for development, **Tailscale** is used for secure remote access, and **SSH** is used to access the terminal and VS Code's Remote-SSH feature.

1.  **Install Tailscale**: On your local machine and the Raspberry Pi, install and set up Tailscale. This creates a secure, private network between your devices.
2.  **Find the IP**: Get the Tailscale IP address of the Raspberry Pi. This can be found in the Tailscale admin panel or by running `tailscale ip -4` on the Pi's terminal.
3.  **Connect with SSH**:
    * **VS Code**: In VS Code, open the Remote Explorer, select "SSH Targets," and add a new host. Enter the SSH command in the format: `ssh pi@<tailscale_ip>`.
    * **Terminal**: Use the command `ssh pi@<tailscale_ip>`.

After connecting, you can navigate to the project directory and run the main application. Note that some hardware components like the LEDs require root privileges, so you must run the main script with `sudo`: `sudo python3 main.py`.

## 🎶 Audio and Sound

The system is designed to provide audio feedback. To ensure this works reliably, the audio session must be active. If the Raspberry Pi is running in a headless state, you may need to first start an audio-playing script to initialize the session before running the main game loop.
