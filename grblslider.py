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
        time.sleep(2)
        self._flush_startup()
        self._send_command("G91")  # set relative mode once


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
    def __init__(self, num_shots, interval, default_exposure=1.0,
                 move_mm_per_shot=10.0, slider_length_mm=134.0, slider_port="/dev/ttyACM0"):
        self.intervalometer = Intervalometer(num_shots, interval, default_exposure)
        self.slider = GRBLSlider(port=slider_port)
        self.num_shots = num_shots
        self.slider_length_mm = slider_length_mm
        self.current_position = 0.0  # start at beginning

        # Adjust move length if needed
        max_possible_moves = slider_length_mm / move_mm_per_shot
        if num_shots - 1 > max_possible_moves:
            self.move_mm_per_shot = slider_length_mm / (num_shots - 1)
            print(f"Adjusted move per shot to {self.move_mm_per_shot:.2f} mm to fit slider length")
        else:
            self.move_mm_per_shot = move_mm_per_shot

    def move_slider_safe(self, distance_mm, feed_rate=100):
        remaining_space = self.slider_length_mm - self.current_position
        if distance_mm > remaining_space:
            distance_mm = remaining_space
        elif distance_mm < -self.current_position:
            distance_mm = -self.current_position

        if distance_mm != 0:
            self.slider.move_mm(distance_mm, feed_rate)
            self.current_position += distance_mm
        else:
            print("Reached slider limit, not moving.")

    def run(self, feed_rate=None):
        """Run the timelapse sequence."""
        for i in range(self.num_shots):
            exposure = self.intervalometer.get_shutter_speed()
            self.intervalometer.trigger_shutter()
            time.sleep(exposure)

            if i != self.num_shots - 1:
                # calculate feed rate if not provided
                if feed_rate is None:
                    remaining_interval = max(0.01, self.intervalometer.interval - exposure)
                    feed_rate_calc = (self.move_mm_per_shot / remaining_interval) * 60  # mm/min
                else:
                    feed_rate_calc = feed_rate

                print(f"Moving slider {self.move_mm_per_shot:.2f} mm at feed {feed_rate_calc:.1f} mm/min")
                self.move_slider_safe(self.move_mm_per_shot, feed_rate_calc)

                time.sleep(max(0, self.intervalometer.interval - exposure))

    def close(self):
        self.slider.close()

# if __name__ == "__main__":
#     num_shots = int(input("Please input your desired number of exposures: "))
#     interval = 5  # seconds between shots
#     move_mm_per_shot = 0.25  # 100 steps equivalent in mm
#     feed_rate = 100  # mm/min

#     timelapse = MotionTimelapse(num_shots, interval, move_mm_per_shot=move_mm_per_shot)
#     try:
#         timelapse.run(feed_rate=feed_rate)
#     finally:
#         timelapse.close()

if __name__ == "__main__":
    # User input
    num_shots = int(input("Enter number of shots: "))
    interval = float(input("Enter interval between shots (seconds): "))
    move_mm_per_shot_guess = 10.0  # initial guess, will be adjusted if needed
    slider_length_mm = 134.0       # total slider travel
    feed_rate = 100                # mm/min

    # Initialize and run timelapse
    timelapse = MotionTimelapse(
        num_shots=num_shots,
        interval=interval,
        move_mm_per_shot=move_mm_per_shot_guess,
        slider_length_mm=slider_length_mm
    )

    try:
        timelapse.run(feed_rate=feed_rate)
    finally:
        timelapse.close()
