import json
import math
from datetime import datetime, timedelta, timezone

#Starting Plane Variables
STARTING_AIRPORT_COORDS = {"lat": 1.12103,"lon": 104.11900} #starting at Hang Nadim Airport, possible addition of other Coords for other starting airports
ROCKET_RELEASE_ALTITUDE = 10000 #written in meters, possible to make 3 optional altitudes depending on choosen air-launch platforms
FLIGHT_DURATION_MINUTES = 5
RETURN_FLIGHT_DURATION_MINUTES = 5

#Parmeters for Rocket
ROCKET_LAUNCH_ANGLE = math.radians(25)
ROCKET_INITIAL_VELOCITY = 5000 #in m/s
G = 9.81 #Gravity
ROCKET_ALTITUDE_CEILING = 200000 #In meters

#Orbit Parameters
EARTH_RADIUS = 6371000  #in meters
ORBIT_ALTITUDE = 200000  #in meters
ORBIT_PERIOD_MINUTES = 90  #in typical LEO orbit
ORBIT_INCLINATION = math.radians(28.5)  # demo inclination

#Time Setup
t0 = datetime.now(timezone.utc)

#Plane Trajectory
plane_points = []
for i in range(FLIGHT_DURATION_MINUTES + 1):
    point_time = t0 + timedelta(minutes=i)
    plane_points.append({
        "time": point_time.isoformat(),
        "lat": STARTING_AIRPORT_COORDS["lat"],
        "lon": STARTING_AIRPORT_COORDS["lon"] + i * 0.05,
        "alt": i * (ROCKET_RELEASE_ALTITUDE / FLIGHT_DURATION_MINUTES)
    })

release_point = plane_points[-1]
release_time = t0 + timedelta(minutes=FLIGHT_DURATION_MINUTES)

for i in range(1, RETURN_FLIGHT_DURATION_MINUTES + 1):
    point_time = release_time + timedelta(minutes=i)
    plane_points.append({
        "time": point_time.isoformat(),
        "lat": release_point["lat"] - i * (release_point["lat"] - STARTING_AIRPORT_COORDS["lat"]) / RETURN_FLIGHT_DURATION_MINUTES,
        "lon": release_point["lon"] - i * (release_point["lon"] - STARTING_AIRPORT_COORDS["lon"]) / RETURN_FLIGHT_DURATION_MINUTES,
        "alt": release_point["alt"] - i * (release_point["alt"] / RETURN_FLIGHT_DURATION_MINUTES)
    })

#Rocket Trajectory
rocket_points = []
payload_points = []
payload_released = False
payload_start_time = None
payload_insertion_coords = None

rocket_duration_sec = 1200

for t in range(0, rocket_duration_sec + 1, 10):
    time = release_time + timedelta(seconds=t)
    x = ROCKET_INITIAL_VELOCITY * math.cos(ROCKET_LAUNCH_ANGLE)
    y = ROCKET_INITIAL_VELOCITY * math.sin(ROCKET_LAUNCH_ANGLE) - 0.5 * G * t ** 2
    alt = release_point["alt"] + y

    #stop when rocket splahes down
    if alt <= 0:
        break

    #Approximate lat/lon shift
    dlon = (x / (111000.0 * math.cos(math.radians(release_point["lat"]))))

    rocket_lat = release_point["lat"]
    rocket_lon = release_point["lon"] + dlon

    rocket_points.append({
        "time": time.isoformat(),
        "lat": rocket_lat,
        "lon": rocket_lon,
        "alt": alt
    })

#Payload Trigger Release
if not payload_released and alt >= ROCKET_ALTITUDE_CEILING:
        payload_released = True
        payload_start_time = time
        payload_insertion_coords = (rocket_lat, rocket_lon)

        # Generate orbit path starting at rocket position
        orbit_period_sec = ORBIT_PERIOD_MINUTES * 60
        num_samples = 180  # 1.5 hours of orbit with 30s step
        for i in range(num_samples):
            tt = i * 30
            t_payload = payload_start_time + timedelta(seconds=tt)
            theta = 2 * math.pi * (tt / orbit_period_sec)

            r = EARTH_RADIUS + ORBIT_ALTITUDE
            lon = (payload_insertion_coords[1] + math.degrees(theta)) % 360

            payload_points.append({
                "time": t_payload.isoformat(),
                "lat": payload_insertion_coords[0],
                "lon": float(lon),
                "alt": ORBIT_ALTITUDE
            })

#Final Data
data = {
    "plane": plane_points,
    "rocket": rocket_points,
    "payload": {
        "track": payload_points,
        "orbit": {
            "inclination": math.degrees(ORBIT_INCLINATION),
            "altitude": ORBIT_ALTITUDE
        },
        "insertion_point": {
            "lat": payload_insertion_coords[0] if payload_insertion_coords else None,
            "lon": payload_insertion_coords[1] if payload_insertion_coords else None,
            "time": payload_start_time.isoformat() if payload_start_time else None
        }
    }
}

with open("trajectory.json", "w") as f:
    json.dump(data, f, indent=2)

print("Trajectory generated to trajectory.json")