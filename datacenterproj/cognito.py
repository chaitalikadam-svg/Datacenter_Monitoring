import hmac
import hashlib
import base64
import boto3
from django.conf import settings
from botocore.exceptions import ClientError

client = boto3.client(
    "cognito-idp",
    region_name=settings.AWS_REGION
)


def get_secret_hash(username):

    message = username + settings.COGNITO_CLIENT_ID

    dig = hmac.new(
        settings.COGNITO_CLIENT_SECRET.encode("utf-8"),
        message.encode("utf-8"),
        hashlib.sha256
    ).digest()

    return base64.b64encode(dig).decode()


def authenticate_user(email, password):

    try:
        response = client.initiate_auth(
            ClientId=settings.COGNITO_CLIENT_ID,
            AuthFlow="USER_PASSWORD_AUTH",
            AuthParameters={
                "USERNAME": email,
                "PASSWORD": password,
                "SECRET_HASH": get_secret_hash(email)
            }
        )

        return response

    except ClientError as e:

        error = e.response["Error"]["Code"]

        if error == "UserNotConfirmedException":
            return "NOT_APPROVED"

        elif error == "NotAuthorizedException":
            return "INVALID_LOGIN"

        elif error == "UserNotFoundException":
            return "USER_NOT_FOUND"

        else:
            return error