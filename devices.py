import subprocess
import fractions
import time
import serial

class Intervalometer:
    def __init__(self, numShots, interval, default_exposure=1.0):
        """
        Initializes the Intervalometer class.
        """
        self.num_shots = numShots
        self.interval = interval
        self.default_exposure = default_exposure
        # self.steps_per_shot = steps_per_shot
        self.set_capture_target()

        # self.slider = StepperSlider(port=slider_port)
    
    # Camera Control Methods
    def set_capture_target(self):
        try:
            subprocess.run(
                ["gphoto2", "--set-config", "capturetarget=1"],
                check=True
            )
        except subprocess.CalledProcessError as e:
            print(f"Error setting capture target: {e.stderr}")
    
    def get_shutter_speed(self):
        """Return the current shutter speed in seconds."""
        try:
            result = subprocess.run(
                ["gphoto2", "--get-config", "shutterspeed"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=True
            )
            for line in result.stdout.splitlines():
                if line.startswith("Current:"):
                    speed_str = line.split("Current:")[1].strip()
                    # Remove trailing 's' if present
                    if speed_str.endswith('s'):
                        speed_str = speed_str[:-1]
                    # Convert to float
                    try:
                        exposure_sec = float(fractions.Fraction(speed_str))
                    except ValueError:
                        exposure_sec = float(speed_str)
                    # Apply default if shorter than 1 second
                    return exposure_sec if exposure_sec > self.default_exposure else self.default_exposure
                return self.default_exposure
        except subprocess.CalledProcessError as e:
            print(f"Error reading shutter speed: {e.stderr}")
            return self.default_exposure
        
    def trigger_shutter(self):
        """Trigger the camera shutter."""
        try:
            subprocess.run(["gphoto2", "--trigger-capture"], check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error triggering shutter: {e.stderr}")
        
    # Main Interval Sequence
    def run_sequence(self):
        """Run the intervalometer sequence."""
        for i in range(self.num_shots):
            exposure = self.get_shutter_speed()
            print(f"Shot {i+1}/{self.num_shots}: Exposure = {exposure:.1f} sec")
            self.trigger_shutter()
            time.sleep(exposure) # Wait for exposure to finish
            if i != self.num_shots - 1:
                time.sleep(self.interval)

class StepperSlider:
    def __init__(self, port="/dev/ttyACM0", baudrate=115200, timeout=2):
        self.ser = serial.Serial(port, baudrate = baudrate, timeout = timeout)
        time.sleep(2) # Wait for Arduino to reset

    def move_steps(self, steps):
        """Move the motor a specific number of steps. Positive = forward."""
        command = f"MOVE {steps}\n"
        self.ser.write(command.encode())

        # Wait for Arduino to confirm move is done
        while True:
            line = self.ser.readline().decode().strip()
            if line == "DONE":
                break
    
    def close(self):
        self.ser.close()

class MotionTimelapse:
    def __init__(self, num_shots, interval, default_exposure=1.0, steps_per_shot=100, slider_port="/dev/ttyACM0"):
        self.intervalometer = Intervalometer(num_shots, interval, default_exposure)
        self.slider = StepperSlider(port=slider_port)
        self.steps_per_shot = steps_per_shot
        self.num_shots = num_shots

    def run(self):
        for i in range(self.num_shots):
            exposure = self.intervalometer.get_shutter_speed()
            print(f"Shot {i+1}/{self.num_shots} | Exposure: {exposure:.3f}s")
            self.intervalometer.trigger_shutter()
            time.sleep(exposure)
            if i != self.num_shots - 1:
                print(f"Moving slider {self.steps_per_shot} steps")
                self.slider.move_steps(self.steps_per_shot)
                time.sleep(max(0, self.intervalometer.interval - exposure))

    def close(self):
        self.slider.close()