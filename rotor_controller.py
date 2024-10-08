import os
import subprocess
import time
import read_file

PAUSE = 850  #change based on satellite velocity 
AZIMUTH_COEFFICIENT = 1 #increase elevation movement for poorly working servo 
ELEVATION_THRESHOLD = 5  # reduce eratic movements in elevation 
ANTENNA_FLIP = True  # TODO: Calculate the flip from the track file
COM_PORT = "COM5"

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

# Example usage: Read azimuth and elevation data from track.txt
os.system('py correct_data.py')
time.sleep(20)
file_path = 'corrected_satellite_data.txt'
azimuth_data, elevation_data = read_file.extract_azimuth_elevation(file_path)

# Generate the Arduino code with actual azimuth and elevation values
generate_arduino_code(azimuth_data, elevation_data)

# Compile and upload the code to Arduino
upload_arduino_code()
