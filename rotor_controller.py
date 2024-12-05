import os
import subprocess
import time


PAUSE = 10000  #change based on satellite velocity   -- 850
AZIMUTH_COEFFICIENT = 1 #increase elevation movement for poorly working servo 
ELEVATION_THRESHOLD = 5  # reduce eratic movements in elevation 
ANTENNA_FLIP = True  # TODO: Calculate the flip from the track file
COM_PORT = "COM3"

def generate_arduino_code(azimuth_data, elevation_data):
    folder_name = "rotor_controller"
    sketch_filename = "rotor_controller.ino"
    
    # Create the folder if it doesn't exist
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)
    
    sketch_path = os.path.join(folder_name, sketch_filename)

    # Store azimuth_data and elevation_data in PROGMEM to reduce SRAM usage
    sketch = f"""
    #include <Servo.h>
    #include <avr/pgmspace.h>

    Servo servo1;  // Servo for azimuth connected to pin 9
    Servo servo2;  // Servo for elevation connected to pin 10

    // Store azimuth and elevation data in flash memory (PROGMEM)
    const int azimuth_data[] PROGMEM = {{{','.join(map(str, azimuth_data))}}};
    const int elevation_data[] PROGMEM = {{{','.join(map(str, elevation_data))}}};

    const int num_steps = {min(len(azimuth_data), len(elevation_data))};
    const int pause = {PAUSE};
    const int elevation_threshold = {ELEVATION_THRESHOLD};
    const int azimuth_coefficient = {AZIMUTH_COEFFICIENT};

    void setup() {{
      servo1.attach(9);
      servo2.attach(10);

      int last_elevation = -1;  // Store the last elevation angle

      for (int i = 0; i < num_steps; i++) {{
        // Retrieve data from flash memory
        int azimuth_angle = pgm_read_word(&azimuth_data[i]);
        int elevation_angle = pgm_read_word(&elevation_data[i]);

        // Move azimuth servo in the opposite direction
        servo1.write(180 - (azimuth_angle * azimuth_coefficient));  
        
        // Only move elevation if the difference is significant
        if (abs(elevation_angle - last_elevation) > elevation_threshold) {{
          servo2.write(elevation_angle);
          last_elevation = elevation_angle;
        }}

        delay(pause);  // Wait between movements
      }}
    }}

    void loop() {{
      // Do nothing in the loop, the code runs once in setup()
    }}
    """
    
    # Write the Arduino sketch to a file
    with open(sketch_path, "w") as file:
        file.write(sketch)


# Function to compile and upload the Arduino sketch using Arduino CLI
def upload_arduino_code():
    folder_name = "rotor_controller"
    
    # Compile the sketch
    compile_command = [
        "arduino-cli", "compile", "--fqbn", "arduino:avr:uno", folder_name
    ]
    subprocess.run(compile_command)

    # Upload the sketch
    upload_command = [
        "arduino-cli", "upload", "-p", COM_PORT, "--fqbn", "arduino:avr:uno", folder_name
    ]
    subprocess.run(upload_command)


def read_satellite_log(file_path):
    azimuths = []
    elevations = []
    
    with open(file_path, "r") as log_file:
        # Skip the header line
        next(log_file)
        
        for line in log_file:
            parts = line.strip().split(", ")
            if len(parts) == 3:
                azimuth = float(parts[1])  # Second column is azimuth
                elevation = float(parts[2])  # Third column is elevation
                azimuths.append(azimuth)
                elevations.append(elevation)
    
    return azimuths, elevations


os.system('py test_pyorbital.py')
time.sleep(1)

log_file_path = "satellite_pass_log.txt"
azimuth_array, elevation_array = read_satellite_log(log_file_path)

print("azimuth array")
print(azimuth_array)

def detect_and_adjust_flip(azimuths):
    adjusted_azimuths = []
    flip_detected = False

    for i, azimuth in enumerate(azimuths):
        if i > 0 and azimuth < azimuths[i - 1]:
            # Flip detected when current azimuth is less than the previous one
            flip_detected = True

        if flip_detected:
            # Adjust the azimuth by adding 360 to account for the flip
            adjusted_azimuths.append(azimuth + 360)
        else:
            adjusted_azimuths.append(azimuth)
    
    return flip_detected, adjusted_azimuths

# Detect and adjust for flip
flip_detected, new_azimuth_array = detect_and_adjust_flip(azimuth_array)

# Output results
print("Flip Detected:", flip_detected)
print("Adjusted Azimuths:", new_azimuth_array)

new_azimuth_array.append(0)
elevation_array.append(0)

#data for troubleshooting tests
azimuth_data = [0, 90, 180, 360, 0]
elevation_data = [10, 20, 30, 40, 0]

# Generate the Arduino code with actual azimuth and elevation values
generate_arduino_code(new_azimuth_array, elevation_array)

# Compile and upload the code to Arduino
upload_arduino_code()
