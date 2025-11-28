"""
Samuel Whitaker
Professor Reynolds
CS111
Brigham Young University
PiLapse - A CS111 Freecoding Project
"""

import serial
import time
from Motor import Motor

# Port constants
PORT = "COM5"
BAUD = 115200
# Max Speed = 2000 (Sourced from Arduino)
# Max Acceleration = 500 (Sourced from Arduino)

### To Build: Default Motor Movements, with allowance
# for custom inputs

# Default Motor Movement Strings
# Set to Zero

# Set Next Step

# Stop
st = "STOP"




if __name__ == "__main__":
    # Open serial connection
    print(f"Connecting to {PORT} at {BAUD} baud...")
    ser = serial.Serial(PORT, BAUD, timeout=1)

    motor = Motor(PORT, BAUD, ser)

    # Give Arduino time to reset
    time.sleep(2)
    print("Connected!")

    motor.send("SPEED 1000", ser)   # Set speed to 1000 steps/sec
    time.sleep(0.1)

    # motor.printStat("SPEED 1000")

    motor.send("ACCEL 300", ser)    # Set acceleration
    time.sleep(0.1)

    motor.send("MOVE 2000", ser)    # Move to position 2000
    time.sleep(3)

    motor.send("MOVE 0", ser)       # Move back to position 0
    time.sleep(3)

    motor.send(st, ser)         # Ramp to a stop
    time.sleep(0.1)

    motor.send("HOME", ser)         # Reset position to 0
    time.sleep(0.1)

    print("Done. Close the program to exit.")