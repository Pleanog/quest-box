import time
from gpiozero import MCP3008

class Joystick:
    """Manages a joystick connected to an MCP3008 ADC with calibration."""

    def __init__(self, x_channel=0, y_channel=1, threshold=0.45, calibration_time=1):
        """
        Initializes the Joystick object and calibrates the center position.

        Args:
            x_channel (int): MCP3008 channel for the X-axis.
            y_channel (int): MCP3008 channel for the Y-axis.
            threshold (float): Threshold for direction detection (0.0-0.5).
            calibration_time (int): Time in seconds to sample for calibration.
        """
        self.joystick_x = MCP3008(channel=x_channel)
        self.joystick_y = MCP3008(channel=y_channel)
        self.threshold = threshold
        self.last_direction = (None, None)
        self.x_offset = 0.0
        self.y_offset = 0.0
        self.calibrate(calibration_time)  # Perform calibration

    def calibrate(self, calibration_time):
        """
        Calibrates the joystick center position by sampling values over time.

        Args:
            calibration_time (int): Time in seconds to sample for calibration.
        """
        print("Calibrating joystick... Please leave the joystick at rest.")
        x_sum = 0.0
        y_sum = 0.0
        samples = 0

        start_time = time.time()
        while time.time() - start_time < calibration_time:
            x_sum += self.joystick_x.value
            y_sum += self.joystick_y.value
            samples += 1
            time.sleep(0.01)

        if samples > 0:
            self.x_offset = x_sum / samples
            self.y_offset = y_sum / samples
            print(f"Calibration complete. X offset: {self.x_offset:.3f}, Y offset: {self.y_offset:.3f}")
        else:
            print("Calibration failed: No samples taken.")

    def read_direction(self):
        """
        Reads the joystick values, applies calibration, and determines the direction.

        Returns:
            tuple: (x_direction, y_direction), where direction is
                   "LEFT", "RIGHT", "UP", "DOWN", or None.
        """
        x_value = self.joystick_x.value - self.x_offset
        y_value = self.joystick_y.value - self.y_offset
        print(f"Raw X: {x_value:.3f}, Y: {y_value:.3f}")

        x_direction = None
        y_direction = None

        if x_value > 0.5 + self.threshold:
            x_direction = "RIGHT"
        elif x_value < 0.5 - self.threshold:
            x_direction = "LEFT"

        if y_value > 0.5 + self.threshold:
            y_direction = "DOWN"
        elif y_value < 0.5 - self.threshold:
            y_direction = "UP"

        return x_direction, y_direction

    def check_state(self):
        """
        Reads the joystick and returns a dictionary of its current state.

        Returns:
            dict: A dictionary with keys 'x_direction' and 'y_direction'.
        """
        x_direction, y_direction = self.read_direction()
        return {"x_direction": x_direction, "y_direction": y_direction}

    def print_direction(self):
        """Prints the joystick direction only when it changes."""
        current_direction = self.read_direction()

        if current_direction != self.last_direction:
            output_string = ""
            if current_direction[0]:
                output_string += current_direction[0]
            if current_direction[1]:
                if output_string:
                    output_string += " "
                output_string += current_direction[1]

            if not output_string:
                print("CENTER")
            else:
                print(output_string)

            self.last_direction = current_direction


if __name__ == "__main__":
    joystick = Joystick()
    print("Starting joystick test. Press Ctrl+C to exit.")
    print("The direction will only be printed when it changes.")
    print("-" * 30)

    try:
        while True:
            joystick.print_direction()
            time.sleep(0.1)

    except KeyboardInterrupt:
        print("\nExiting program.")

    finally:
        joystick.joystick_x.close()
        joystick.joystick_y.close()
        print("GPIOs cleaned up.")