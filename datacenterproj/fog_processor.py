from datetime import datetime

BUFFER = {}
WINDOW_SIZE = 10
# Number of readings to accumulate before computing aggregated metrics


def process_sensor_data(data): #computes the average metrics 

    rack_id = data["rack_id"]

    if rack_id not in BUFFER:
        BUFFER[rack_id] = []

    BUFFER[rack_id].append(data)

    if len(BUFFER[rack_id]) >= WINDOW_SIZE:

        records = BUFFER[rack_id]

        avg_inlet = sum(r["temp_inlet"] for r in records) / WINDOW_SIZE
        avg_outlet = sum(r["temp_outlet"] for r in records) / WINDOW_SIZE
        avg_temperature = (avg_inlet + avg_outlet) / 2
        avg_humidity = sum(r["humidity"] for r in records) / WINDOW_SIZE
        avg_power = sum(r["power_usage"] for r in records) / WINDOW_SIZE
        avg_cpu = sum(r["cpu_utilization"] for r in records) / WINDOW_SIZE
        avg_network = sum(r["network_io"] for r in records) / WINDOW_SIZE

        fog_payload = {
            "timestamp": datetime.utcnow().isoformat(),
            "rack_id": rack_id,
            "avg_temperature": round(avg_temperature, 2),
            "avg_humidity": round(avg_humidity, 2),
            "avg_power_usage": round(avg_power, 2),
            "avg_cpu_utilization": round(avg_cpu, 2),
            "avg_network_io": round(avg_network, 2),
        }

        BUFFER[rack_id] = []

        return fog_payload

    return None