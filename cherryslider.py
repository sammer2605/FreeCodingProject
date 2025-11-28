from devices import Intervalometer

# Request user input
num_shots = int(input("What is your desired number of exposures? "))
interval = int(input("What is your desired interval between exposures? "))

# Create an intervalometer instance
timelapse = Intervalometer(num_shots, interval)

# Run the sequence
timelapse.run_sequence()