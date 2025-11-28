import subprocess
import fractions
import time

class Intervalometer:
    def __init__(self, numShots, interval, default_exposure=1.0):
        """
        Initializes the Intervalometer class.
        """
        self.num_shots = numShots
        self.interval = interval
        self.default_exposure = default_exposure
        self.set_capture_target()
    
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