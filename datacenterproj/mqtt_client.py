import ssl
import json
import paho.mqtt.client as mqtt

AWS_ENDPOINT = "a29go9u8udl3o3-ats.iot.us-east-1.amazonaws.com"
PORT = 8883
TOPIC = "datacenter/fog/telemetry"

CA_PATH = "certs/AmazonRootCA1.pem"
CERT_PATH = "certs/fog_node_01.cert.pem"
KEY_PATH = "certs/fog_node_01.private.key"


client = mqtt.Client()

client.tls_set(
    CA_PATH,
    certfile=CERT_PATH,
    keyfile=KEY_PATH,
    tls_version=ssl.PROTOCOL_TLSv1_2
)

client.connect(AWS_ENDPOINT, PORT)


def publish_to_iot(payload):

    client.publish(TOPIC, json.dumps(payload))