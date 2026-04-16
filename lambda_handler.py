import boto3

sns = boto3.client("sns")

TOPIC_ARN = "arn:aws:sns:us-east-1:527878813098:datacenter-alerts"


def lambda_handler(event, context):

    alerts = []

    for record in event["Records"]:

        if record["eventName"] != "INSERT":
            continue

        new_data = record["dynamodb"]["NewImage"]

        # Extract values
        rack_id = new_data["rack_id"]["S"]

        cpu = float(new_data["avg_cpu_utilization"]["N"])
        network = float(new_data["avg_network_io"]["N"])
        humidity = float(new_data["avg_humidity"]["N"])
        power = float(new_data["avg_power_usage"]["N"])
        temperature = float(new_data["avg_temperature"]["N"])

 
        if cpu > 90:
            alerts.append(f"CPU High: {cpu}%")

        if network > 800:
            alerts.append(f"Network I/O High: {network} Mbps")

        if humidity > 75:
            alerts.append(f"Humidity High: {humidity}%")

        if power > 5:
            alerts.append(f"Power High: {power}W")

        if temperature > 32:
            alerts.append(f"Temperature High: {temperature}°C")

        if alerts:

            message = f"""
 DATACENTER ALERT 

Rack: {rack_id}

Issues:
{chr(10).join(alerts)}

Immediate attention required!
"""

            sns.publish(
                TopicArn=TOPIC_ARN,
                Subject="Datacenter Alert ",
                Message=message
            )

    return {"status": "done"}