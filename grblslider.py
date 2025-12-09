import subprocess
import fractions
import time
import serial

class Intervalometer:
    """Controls camera triggering and exposure reading via gphoto2."""
    def __init__(self, num_shots, interval, default_exposure=1.0):
        self.num_shots = num_shots
        self.interval = interval
        self.default_exposure = default_exposure
        self.set_capture_target()

    def set_capture_target(self):
        """Set camera to save images to memory card (capture target 1)."""
        try:
            subprocess.run(
                ["gphoto2", "--set-config", "capturetarget=1"],
                check=True
            )
        except subprocess.CalledProcessError as e:
            print(f"Error setting capture target: {e.stderr}")

    def get_shutter_speed(self):
        """Return current shutter speed in seconds."""
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
                    if speed_str.endswith('s'):
                        speed_str = speed_str[:-1]
                    try:
                        exposure_sec = float(fractions.Fraction(speed_str))
                    except ValueError:
                        exposure_sec = float(speed_str)
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

class GRBLSlider:
    """Controls a GRBL-based slider in millimeters."""
    def __init__(self, port="/dev/ttyACM0", baudrate=115200, timeout=2):
        self.ser = serial.Serial(port, baudrate=baudrate, timeout=timeout)
        time.sleep(2)  # wait for Arduino to reset
        self._flush_startup()

    def _flush_startup(self):
        while self.ser.in_waiting:
            self.ser.readline()

    def _send_command(self, command):
        self.ser.write((command + '\n').encode())
        while True:
            line = self.ser.readline().decode().strip()
            if line:
                if 'ok' in line.lower():
                    break
                elif 'error' in line.lower():
                    raise RuntimeError(f"GRBL error: {line}")

    def move_mm(self, distance_mm, feed_rate=100):
        """Move slider relative distance in mm at given feed rate (mm/min)."""
        self._send_command("G91")  # relative positioning
        self._send_command(f"G1 X{distance_mm} F{feed_rate}")

    def home(self):
        """Home slider if limit switches installed."""
        self._send_command("$H")

    def close(self):
        self.ser.close()

class MotionTimelapse:
    """Runs a motion-controlled timelapse sequence."""
    def __init__(self, num_shots, interval, default_exposure=1.0,
                 move_mm_per_shot=0.25, slider_port="/dev/ttyACM0"):
        self.intervalometer = Intervalometer(num_shots, interval, default_exposure)
        self.slider = GRBLSlider(port=slider_port)
        self.move_mm_per_shot = move_mm_per_shot
        self.num_shots = num_shots

    def run(self, feed_rate=100):
        """Run the full timelapse sequence."""
        for i in range(self.num_shots):
            exposure = self.intervalometer.get_shutter_speed()
            print(f"Shot {i+1}/{self.num_shots} | Exposure: {exposure:.3f}s")
            self.intervalometer.trigger_shutter()
            time.sleep(exposure)
            if i != self.num_shots - 1:
                print(f"Moving slider {self.move_mm_per_shot} mm")
                self.slider.move_mm(self.move_mm_per_shot, feed_rate)
                time.sleep(max(0, self.intervalometer.interval - exposure))

    def close(self):
        self.slider.close()

# Example usage
if __name__ == "__main__":
    num_shots = 10
    interval = 5  # seconds between shots
    move_mm_per_shot = 0.25  # 100 steps equivalent in mm
    feed_rate = 100  # mm/min

    timelapse = MotionTimelapse(num_shots, interval, move_mm_per_shot=move_mm_per_shot)
    try:
        timelapse.run(feed_rate=feed_rate)
    finally:
        timelapse.close()
