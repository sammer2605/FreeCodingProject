class Motor:
    def __init__(self, port, baud, serial):
        self.port = port
        self.baud = baud
        self.serial = serial

    def __str__(self):
        print(f'{self} object at port {self.port} with {self.baud} baud.')

    # Print current motor status
    def printStat(self, cmd):
        """Prints the current status of the motor controller."""
        print(f"Motor Status: \"{cmd}\"")

    # Port command to Arduino Motor Controller
    def send(self, cmd, ser):
        """Send a command to the Arduino via USB connection"""
        full = cmd + "\n"
        ser.write(full.encode("utf-8"))
        self.printStat(cmd)

        
    