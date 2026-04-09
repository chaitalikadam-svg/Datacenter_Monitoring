import requests
import random
import time
from datetime import datetime

URL = "http://FogEdgeDataCenterMonitoring-env.eba-w5x6nbdb.us-east-1.elasticbeanstalk.com/sensor-data/"

#URL = "http://127.0.0.1:8080/sensor-data/"


RACK_COUNT = 2
SLEEP_INTERVAL = 2  #seconds

def generate_sensor_payload(rack_id):
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "rack_id": f"RACK-{rack_id:02d}",

        # inlet and outlet temp
        "temp_inlet": round(random.uniform(20, 28), 2),
        "temp_outlet": round(random.uniform(30, 45), 2),

        # 6 sensors
        "humidity": round(random.uniform(35, 60), 2),
        "power_usage": round(random.uniform(2, 5), 2),
        "cpu_utilization": round(random.uniform(10, 90), 2),
        "network_io": round(random.uniform(100, 900), 2),
        "smoke_detected": 0, 
        "water_leak": 0    
    }

while True:
    for rack in range(1, RACK_COUNT + 1):

        data = generate_sensor_payload(rack)

        response = requests.post(URL, json=data)

        print("Sent to backend:", response.status_code, data)

    time.sleep(SLEEP_INTERVAL)