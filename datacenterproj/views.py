from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .fog_processor import process_sensor_data
from .mqtt_client import publish_to_iot
import json
import boto3
from django.shortcuts import render, redirect
from .dashdynamodb import get_all_data
from .cognito import authenticate_user, get_secret_hash
from django.conf import settings
from botocore.exceptions import ClientError
from django.conf import settings

# Clients
cognito = boto3.client("cognito-idp", region_name=settings.AWS_REGION)
sns = boto3.client("sns", region_name=settings.AWS_REGION)
TOPIC_ARN = "arn:aws:sns:us-east-1:527878813098:datacenter-alerts"

def signup_view(request):

    if request.method == "POST":

        email = request.POST.get("email")
        password = request.POST.get("password")

        # Check if user exists in Cognito user group
        try:
            cognito.admin_get_user(
                UserPoolId=settings.COGNITO_USER_POOL_ID,
                Username=email
            )

            return render(request, "signup.html", {
                "error": "User already exists. Please sign in."
            })

        except cognito.exceptions.UserNotFoundException:
            pass

        except Exception as e:
            return render(request, "signup.html", {"error": str(e)})

        # Creation of user
        try:
            cognito.sign_up(
                ClientId=settings.COGNITO_CLIENT_ID,
                Username=email,
                Password=password,
                SecretHash=get_secret_hash(email),  # remove if no secret
                UserAttributes=[
                    {"Name": "email", "Value": email}
                ]
            )

        except ClientError as e:
            return render(request, "signup.html", {
                "error": e.response["Error"]["Message"]
            })

        # Check if already subscribed to SNS topic
        try:
            subs = sns.list_subscriptions_by_topic(TopicArn=TOPIC_ARN)

            already_subscribed = False

            for sub in subs["Subscriptions"]:
                if sub["Endpoint"] == email:
                    already_subscribed = True
                    break

            # Subscribe if NOT already subscribed to the SNS
            if not already_subscribed:
                sns.subscribe(
                    TopicArn=TOPIC_ARN,
                    Protocol="email",
                    Endpoint=email
                )
                message = "Signup successful! Please confirm email subscription."
            else:
                message = "Signup successful! You are already subscribed. Please login."

        except Exception as e:
            print("SNS ERROR:", e)
            message = "Signup successful, but SNS subscription failed."


        return render(request, "login.html", {
            "message": message
        })

    return render(request, "signup.html")

def login_view(request):

    if request.method == "POST":

        email = request.POST.get("email")
        password = request.POST.get("password")
        

        result = authenticate_user(email, password)
        
        if result == "NOT_APPROVED": 
            return render(request, "login.html", {
                "error": "Admin has not approved your account yet"
            })

        if result == "INVALID_LOGIN":
            return render(request, "login.html", {
                "error": "Invalid email or password"
            })

        if result == "USER_NOT_FOUND":
            return render(request, "login.html", {
                "error": "User does not exist"
            })

        return redirect("dashboard")

    return render(request, "login.html")

@csrf_exempt
def receive_sensor_data(request):

    if request.method == "POST":

        data = json.loads(request.body)

        processed = process_sensor_data(data)

        if processed:
            print("Fog processed:", processed)

            # send data to AWS IoT Core
            publish_to_iot(processed)

        return JsonResponse({"status": "received"})

def rack_data_api(request):
    try:
        data = get_all_data() or []

        racks = {}

        # Group by rack_id
        for item in data:
            rack = item.get("rack_id", "unknown")
            racks.setdefault(rack, []).append(item)

        for rack in racks:
            racks[rack] = sorted(
                racks[rack],
                key=lambda x: x.get("timestamp", "")
            )

        return JsonResponse({"racks": racks})

    except Exception as e:
        print("ERROR in rack_data_api:", e)
        return JsonResponse({"error": "Internal server error"}, status=500)
    
def dashboard(request):
    # Display dashboard
    return render(request, "dashboard.html")
