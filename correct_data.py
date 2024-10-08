import re

THRESHOLD = 6   #TODO: put in configuration file

def correct_azimuth(azimuth):
    """Correct azimuth by flipping values > 180 degrees to negative equivalents."""
    if azimuth > 180:
        return azimuth - 360
    return azimuth

def process_file(input_file, output_file):
    with open(input_file, 'r') as infile, open(output_file, 'w') as outfile:
        lines = infile.readlines()
        
        for line in lines:
            # Match lines with azimuth data (avoid header lines)
            match = re.match(r"(\S+\s+\S+)\s+([\d.]+)\s+([\d.]+)", line)
            if match:
                timestamp, azimuth, elevation = match.groups()
                azimuth = float(azimuth)
                elevation = float(elevation)
                
                # Correct azimuth crossing 0°
                corrected_azimuth = correct_azimuth(azimuth)
                
                # Write the corrected data
                outfile.write(f"{timestamp}\t{corrected_azimuth:.2f}\t{elevation:.2f}\n")
            else:
                # Write header or non-data lines as they are
                outfile.write(line)
