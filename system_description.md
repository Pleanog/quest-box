### 📘 Quest-Box Project Documentation

#### **Overview**
Quest-Box is an interactive, story-driven puzzle box prototype built on the Raspberry Pi. It integrates various hardware inputs and outputs with AI-generated content to create a dynamic and immersive game experience. The system is designed to be modular and scalable, allowing for the easy integration of new sensors, actuators, and narrative components.

---

#### **System Architecture & Data Flow**

The system operates on a multi-threaded architecture to handle asynchronous input/output operations without blocking the main game loop.

1.  **`main.py`** -   This is the central orchestrator of the system.
    -   It initializes the **Input Manager** (`InputManager`), the **Output Manager** (`OutputManager`), and the **Game Sequence** (`GameSequence`).
    -   It loads the game configuration from a JSON file (e.g., `gemini-api/room-small.json`).
    -   It creates and manages `Queue` objects for inter-thread communication:
        -   `input_event_queue`: Transports input events from hardware controllers to the game logic.
        -   `output_command_queue`: Transports commands from the game logic to the output actuators.
    -   It starts the `InputManager` and `OutputManager` in their own dedicated threads to allow for continuous, non-blocking polling and command execution.
    -   The main thread then runs the `GameSequence.run_sequence()` loop, which processes events from the `input_event_queue` and sends commands to the `output_command_queue`.

2.  **`InputManager`** -   Manages all physical input devices (buttons, gyro, encoders, distance sensor).
    -   It instantiates and controls a separate class for each type of device (e.g., `SX1509`, `Gyro`, `RotaryEncoderController`).
    -   It runs a continuous polling loop (for certain devices like I2C sensors) or starts individual threads (for devices like rotary encoders) to monitor for events.
    -   Upon detecting a valid hardware event, it creates an `InputEvent` object and places it into the `input_event_queue`.

3.  **`OutputManager`** -   Manages all physical output devices (LEDs, vibration motors, speakers).
    -   It maintains a registry of hardware controllers (e.g., `LEDController`, `VibrationController`).
    -   It runs a separate thread that continuously checks the `output_command_queue` for new commands.
    -   When a command is received, it routes the command to the appropriate hardware controller for execution.

4.  **`GameSequence`** -   This class contains the core game logic.
    -   It reads and parses the `solution_sequence` from the loaded JSON configuration.
    -   It processes events from the `input_event_queue` in the order specified by the solution sequence.
    -   It validates that incoming events match the expected sensor type and value for the current step.
    -   If an input is correct, it advances to the next step; otherwise, it handles a retry or game-over state.
    -   It sends commands to the `output_command_queue` to trigger effects, hints, or final success states.

---

#### **Hardware & Configuration Details**

-   **I2C Bus:** The project uses a single I2C bus with a shared `I2C_BUS_LOCK` to prevent communication conflicts between multiple I2C devices (e.g., the gyro and the SX1509).
-   **Device Configuration:** All hardware devices are defined in a single `device_configs` list within `main.py`. This central list makes it easy to add or modify devices without changing other parts of the code.
-   **Audio:** To use the audio functionality (if implemented), a desktop audio session must be active on the Raspberry Pi. This can be initiated by starting a desktop environment and playing audio from a separate application before running the main script.
-   **LEDs:** Due to low-level GPIO access requirements, the `main.py` or `LEDController` script needs to be run with **`sudo`** to control the LEDs. This is a common requirement for the RPi.GPIO library.
-   **JSON Validation:** The `GameSequence` class uses a `SENSOR_REGISTRY` to validate that the sensor types and their required parameters from the JSON configuration are correctly defined.

---

#### **Planned Expansions**
-   **Dynamic Content:** AI services (e.g., Google Gemini) will dynamically generate new rooms and puzzles.
-   **Voice and Audio:** Integration of ElevenLabs for real-time voice narration and a dedicated audio controller for sound effects.
-   **Branching Logic:** Expansion of the JSON format to support branching storylines and multiple paths.
-   **Automated Testing:** Implementation of a "Demo Mode" with static JSON files for reliable testing before deploying AI-generated content.