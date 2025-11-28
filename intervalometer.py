"""
Name: Samuel Whitaker
Professor: Michael Reynolds
Course: CS 111
Project: Free-Coding Project
Description: This segment of code builds an intervelometer program
to operate a camera on desired intervals. Because it is being built
from scratch, I can play with more precise intervals (which should
hopefully result in smoother motion in timelapse films.)
"""
# Import time for timing purposes (lol)
import time
# Import subprocess to relay commands to camera
import subprocess
# Import fractions to interpret camera shutter speed data
import fractions

### Setup Functions ###
def setDelay():
    '''Returns the desired delay time as an integer value.'''
    return int(input("Please enter the starting delay: "))

def setExposure():
    '''Returns the desired exposure time as a float value.'''
    return float(input("Please enter your exposure length: "))

def setInterval():
    '''Returns the desired interval between exposures as an integer value.'''
    return int(input("Please enter the interval between shots (sec greater than 1): "))

def setNumShots():
    '''Returns the desired number of shots as an integer value.'''
    return int(input("Please enter the desired number of shots: "))

def setFps():
    '''Returns the frames-per-second (FPS) value of the final clip as an integer value.'''
    return int(input("Please enter the video FPS: "))

### Camera Control ###
def trigger_camera():
    subprocess.run(["gphoto2", "--trigger-capture"], check=True)

def get_shutter_speed(default=1.0):
    """
    Queries the Nikon Z7 via gphoto2 and returns the current shutter speed in seconds.
    - Defaults to `default` (1 second) for exposures shorter than that.
    - Handles fractions, decimals, or values with 's' suffix.
    """
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

                # Use the actual exposure only if it's above default
                return exposure_sec if exposure_sec > default else default

        # Fallback if Current not found
        print("Warning: Could not find current shutter speed, using default 1 sec.")
        return default

    except subprocess.CalledProcessError as e:
        print(f"Error reading shutter speed: {e.stderr}")
        return default
def runSequence(delay, exp, interval, num):
    '''Runs the sequence.'''
    print(f"\nWaiting {delay} seconds before starting...")
    time.sleep(delay)

    for i in range(1, num + 1):
        print(f"Shot {i+1}: Exposure = {exp:.1f} seconds.")
        print(f"Capturing shot {i}/{num}...")
        # Trigger the shutter
        trigger_camera()
        # Wait for exposure to finish
        time.sleep(exp)
        # Interval
        if i != num: 
            time.sleep(interval)
    print("\nSequence complete!")

### Calculations ###
def calcClipTime(numShots, fps):
    '''Calculates the total length of the final timelapse sequence.'''
    clipTime = numShots / fps
    return clipTime

def calcTotTime(delay, exp, intvl, numShots):
    '''Calculate the total runtime of the sequence and estimate
    an endtime based on the current time.'''
    return delay + numShots * (exp + intvl)


if __name__ == "__main__":
    delay = setDelay()
    exp = get_shutter_speed(default=1.0)
    interval = setInterval()
    num = setNumShots()
    fps = setFps()

    clipSeconds = print(f"\nYour timelapse clip will be {calcClipTime(num, fps):.2f} seconds long.")
    print(f"Your clip will be {calcClipTime(num, fps):.1f} seconds long.")
    runSequence(delay, exp, interval, num)
