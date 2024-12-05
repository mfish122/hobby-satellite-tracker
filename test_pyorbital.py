from pyorbital.orbital import Orbital
from datetime import datetime, timedelta, timezone

LATITUDE = 45.677
LONGITUDE = -121.864
ALTITUDE = 0  # Observer altitude in kilometers
SATELLITE = "NOAA 15"
LOG_FILE = "satellite_pass_log.txt"
TIME_INTERVAL = 10

# Directly include TLE data for NOAA 15
TLE_LINE1 = "1 56196U 23054U   24025.24529908  .00024647  00000-0  76331-3 0  9999"
TLE_LINE2 = "2 56196  97.3813 283.1116 0007209 337.8726  22.2205 15.33421680 44077"

# Create an Orbital object for the satellite using the TLE data
orb = Orbital(SATELLITE, line1=TLE_LINE1, line2=TLE_LINE2)

# Get the current UTC time
today = datetime.now(timezone.utc)

# Get the next passes
z = orb.get_next_passes(today, 24, LATITUDE, LONGITUDE, ALTITUDE, tol=0.001, horizon=0)

# Extract start and end times for the first pass
start_time = z[0][0].replace(tzinfo=timezone.utc)
end_time = z[0][1].replace(tzinfo=timezone.utc)

print(f"Pass start time is: {start_time}")
print(f"Pass end time is: {end_time}")

# Open the log file for writing
with open(LOG_FILE, "w") as log_file:
    log_file.write("Time, Azimuth, Elevation\n")  # Header

    current_time = start_time
    while current_time <= end_time:
        azimuth, elevation = orb.get_observer_look(current_time, LATITUDE, LONGITUDE, ALTITUDE)
        log_file.write(f"{current_time}, {azimuth:.2f}, {elevation:.2f}\n")
        print(f"Time: {current_time}, Azimuth: {azimuth:.2f}, Elevation: {elevation:.2f}")
        
        # Increment the time by 10 seconds
        current_time += timedelta(seconds=TIME_INTERVAL)

print(f"Azimuth and elevation data logged to {LOG_FILE}")

