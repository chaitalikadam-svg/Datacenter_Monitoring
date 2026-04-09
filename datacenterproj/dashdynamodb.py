import boto3
from django.conf import settings

dynamodb = boto3.resource(
    "dynamodb",
    region_name=settings.AWS_REGION
)

table = dynamodb.Table("Datacenter_Sensors")


def get_all_data():
    response = table.scan()
    return response.get("Items", [])