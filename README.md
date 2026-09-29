# Fog and Edge Based Datacenter Monitoring and Alert System

A hierarchical **edge → fog → cloud** monitoring platform for datacenter environments. Simulated rack sensors stream telemetry to a fog node that filters and aggregates it locally. Only the aggregated data is sent to AWS, where it is stored, visualised on a live dashboard, and checked against thresholds to trigger real-time email alerts.

---

## Table of Contents

- [Motivation](#motivation)
- [Features](#features)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [How It Works](#how-it-works)
- [Alert Thresholds](#alert-thresholds)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [CI/CD Pipeline](#cicd-pipeline)
- [Security](#security)

---

## Motivation

Purely cloud-based monitoring struggles with high latency, wasted bandwidth, single points of failure during outages, slow alert response, and poor scalability as device counts grow. Fog and edge computing addresses this by moving computation close to the data source:

- **Edge** nodes generate and forward raw sensor readings.
- **Fog** nodes preprocess, denoise and aggregate the data before it leaves the site.
- **Cloud** services handle durable storage, visualisation and alerting.

## Features

- Simulated datacenter telemetry (CPU, power, network, humidity, inlet/outlet temperature, smoke, water leakage) every 2 seconds per rack
- Fog-level sliding-window aggregation (10 readings per rack) to cut bandwidth and sensor noise
- Secure MQTT ingestion into AWS IoT Core using mutual TLS (X.509 certificates)
- Automatic routing of telemetry to DynamoDB via an IoT Rule
- Event-driven anomaly detection with DynamoDB Streams and AWS Lambda
- Email alerts to subscribed users through Amazon SNS
- User registration and login with Amazon Cognito, with **manual admin approval** before access is granted
- Real-time Chart.js dashboard (refreshes every 5 seconds, 40-point moving window) with per-rack drill-down for RACK-01 and RACK-02
- Automated deployment to AWS Elastic Beanstalk via GitHub Actions

## Architecture

![Architecture Diagram](architecture.png)


## Tech Stack

| Layer | Technology |
|---|---|
| Edge / Fog | Python (`sensors.py`, `fogprocessor.py`), HTTP, MQTT |
| Ingestion | AWS IoT Core, IoT Rules |
| Storage | Amazon DynamoDB (partition key `rack_id`, sort key `timestamp`) |
| Alerting | DynamoDB Streams, AWS Lambda, Amazon SNS |
| Auth | Amazon Cognito User Pools (`USER_PASSWORD_AUTH` with HMAC secret hash) |
| Backend | Django (REST endpoints), `boto3` |
| Frontend | Chart.js |
| Hosting | AWS Elastic Beanstalk (Python 3.12, ALB + auto-scaling on EC2) |
| CI/CD | GitHub Actions, Elastic Beanstalk CLI |

## How It Works

1. **Edge – data generation.** `sensors.py` simulates rack sensors and emits timestamped (UTC) JSON payloads with a rack ID every 2 seconds. Payloads are sent to the fog node over lightweight HTTP.
2. **Fog – aggregation.** `fogprocessor.py` keeps a separate buffer per rack. When a buffer reaches 10 readings, it computes averages (for example inlet/outlet temperature, CPU, humidity, power, network), stamps the result with UTC time, clears the buffer and forwards one aggregated payload.
3. **Cloud – ingestion.** The fog node publishes to the MQTT topic `datacenter/fog/telemetry` on AWS IoT Core over mutual TLS (Amazon root CA, device certificate, private key).
4. **Cloud – storage.** An IoT Rule (`SELECT`) writes every message into the DynamoDB table `Datacenter_Sensors`.
5. **Alerting.** A new DynamoDB record triggers a Lambda function through DynamoDB Streams. Lambda compares the readings against thresholds and, on a breach, publishes a summary (rack ID and issues) to an SNS topic, which emails all subscribers.
6. **Dashboard.** The Django backend exposes `/api/rack-data/`, secured by Cognito tokens. The frontend polls it every 5 seconds and updates the rack status cards and time-series charts without page reloads.

### Sample aggregated payload

```json
{
  "timestamp": "2026-04-16T17:21:26.951422",
  "rack_id": "RACK-01",
  "avg_temperature": 31.19,
  "avg_humidity": 47.83,
  "avg_power_usage": 3.92,
  "avg_cpu_utilization": 47.78,
  "avg_network_io": 491.44
}
```


## Alert Thresholds

Configured in the Lambda function:

| Metric | Alert when |
|---|---|
| CPU utilisation | > 90 % |
| Network | > 800 Mbps |
| Humidity | > 75 % |
| Power usage | > 5 kW |
| Temperature | > 32 °C |

Example alert email:

```
DATACENTER ALERT

Rack: RACK-02
Issues:
Temperature High: 32.06°C
```



## Getting Started

### Prerequisites

- Python 3.12
- An AWS account with permissions for IoT Core, DynamoDB, Lambda, SNS, Cognito and Elastic Beanstalk
- AWS CLI and EB CLI (`pip install awsebcli`)
- IoT Core device certificate, private key and Amazon root CA for the fog node

### 1. Clone and install

```bash
git clone https://github.com/Chaitali-Kadam1008/Datacenter_Monitoring.git
cd Datacenter_Monitoring
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
```

### 2. Provision AWS resources

1. **DynamoDB:** create table `Datacenter_Sensors` with partition key `rack_id` (String) and sort key `timestamp` (String). Enable **DynamoDB Streams**.
2. **IoT Core:** register the fog node as a Thing, attach a policy, and download the certificates. Create an IoT Rule that selects messages from `datacenter/fog/telemetry` and writes them to `Datacenter_Sensors`.
3. **SNS:** create a topic for datacenter alerts and subscribe user emails to it.
4. **Lambda:** deploy the threshold-checking function, add the DynamoDB Stream as its trigger, and give it permission to publish to the SNS topic (least-privilege IAM role).
5. **Cognito:** create a User Pool and an app client **with a client secret**, and enable `USER_PASSWORD_AUTH`.

### 3. Configure environment variables

Set these locally or in Elastic Beanstalk (names are suggestions; match your code):

```bash
AWS_REGION=us-east-1
COGNITO_USER_POOL_ID=<user-pool-id>
COGNITO_CLIENT_ID=<app-client-id>
COGNITO_CLIENT_SECRET=<app-client-secret>
DYNAMODB_TABLE=Datacenter_Sensors
IOT_ENDPOINT=<your-iot-endpoint>-ats.iot.us-east-1.amazonaws.com
```

### 4. Run the Django backend

```bash
python manage.py migrate
python manage.py runserver
```

Open <http://127.0.0.1:8000/>.

### 5. Start the fog processor, then the sensors

```bash
python fog/fogprocessor.py   # aggregates and publishes to AWS IoT Core
python edge/sensors.py       # generates readings every 2 seconds
```

### 6. Register a user

1. Sign up through the application.
2. An administrator confirms the user in the Cognito console (until then, login returns `NOT_APPROVED`).
3. Subscribe to the SNS topic to receive alert emails, then log in to view the dashboard.

## CI/CD Pipeline

Deployment is automated with **GitHub Actions** (`.github/workflows/`), triggered by a push to `main` or a merged pull request into `main`.

Steps: checkout → set up Python 3.12 → install EB CLI → configure AWS credentials → `eb init` / `eb use` / `eb deploy --label "deploy-<run_id>"`.

Add these **GitHub Secrets** to the repository:

| Secret | Purpose |
|---|---|
| `AWS_ACCESS_KEY_ID` | AWS credentials |
| `AWS_SECRET_ACCESS_KEY` | AWS credentials |
| `AWS_SESSION_TOKEN` | Needed for temporary/learner-lab credentials |
| `AWS_REGION` | Deployment region |
| `EB_APP_NAME` | Elastic Beanstalk application name |
| `EB_ENV_NAME` | Elastic Beanstalk environment name |

Each deployment is labelled with its GitHub Actions run ID, which gives traceability and easy rollback.

## Security

- Device ↔ IoT Core traffic uses mutual TLS with X.509 certificates.
- Cognito handles authentication with token-based (JWT) access; the app computes an HMAC-SHA256 secret hash so only the legitimate backend can call the auth flow.
- Admin-approval flow prevents unauthorised access to monitoring data.
- Least-privilege IAM roles restrict access to DynamoDB, Lambda and SNS.
- Credentials for CI/CD live in GitHub Secrets, never in the codebase.
