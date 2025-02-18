# Backend Assignment - Trigger Service

## Event Trigger Platform

This project is an event trigger platform where users can create, manage, and trigger events based on predefined conditions.

### Features
- **Scheduled Triggers:** Fire at a fixed time or at intervals (one-time or recurring).
- **API Triggers:** Fire upon receiving an API request with predefined payload.
- **Event Logs:** Maintain logs for triggered events, stored for 2 hours (active), archived for 46 hours, and deleted after 48 hours.
- **CRUD Operations:** Create, update, delete, and fetch triggers.
- **Minimal UI:** Swagger UI/OpenAPI Spec for API interaction.
- **Authentication:** Token-based authentication.
- **Containerized Deployment:** Works locally using Docker.

---
## API Usage

### 1. Authentication
Before using the APIs, generate an access token:
```http
GET http://0.0.0.0:8989/generate_token?passcode=11923
```
_Response:_
```json
{"access_token": "your_token_here"}
```
Include this token in the `Authorization` header for all subsequent requests.

### 2. Create a Trigger
#### One-time Scheduled Trigger
```http
POST http://0.0.0.0:8989/triggers/create_trigger
Content-Type: application/json
Authorization: Bearer <your_token>
```
```json
{
  "trigger_name": "rohith",
  "trigger_time": "2025-02-16-17:37"
}
```

#### Interval-based Scheduled Trigger
```json
{
  "trigger_name": "rohith",
  "interval": 5
}
```
_Interval is in minutes._

#### API Trigger
```json
{
  "trigger_name": "rohith",
  "api_payload": {"pay_load": 123}
}
```

### 3. Fetch All Triggers
```http
GET http://0.0.0.0:8989/triggers/fetch
Authorization: Bearer <your_token>
```

### 4. Edit a Trigger
```http
PATCH http://0.0.0.0:8989/triggers/update_trigger?trigger_id=123
Authorization: Bearer <your_token>
```
_Editable fields: trigger name, time, interval, API payload._

### 5. Delete a Trigger
```http
DELETE http://0.0.0.0:8989/triggers/delete_trigger?trigger_id=1
Authorization: Bearer <your_token>
```

### 6. Fetch Event Logs
```http
GET http://0.0.0.0:8989/triggered_events/fetch_events
Authorization: Bearer <your_token>
```
---
## Setup & Deployment

### 1. Local Setup (Using Docker)
Ensure Docker is installed, then run:
```sh
git clone <repo_url>
cd event-trigger-platform
sudo docker build -t trigger-service .
sudo docker run -p 8989:8989 trigger-service
```

The app will be accessible at `http://localhost:8989`

### 2. Deployment
The app is deployed on Render (free tier). Access it here:
[Live Demo](https://trigger-service-lsma.onrender.com)
[Local Demo](http://0.0.0.0:8989)

---
## Cost Estimation
### Running Cost for 30 Days (5 queries/day)
| Resource                        | Provider | Cost |
|---------------------------------|----------|------|
| Render (Free Tier)              | Hosting | 0 rs |
| PostgreSQL (Free Tier)          | Database | 0 rs |
| PostgreSQL (Free Tier)          | Database | 0 rs |
| RabbitMQ -CloudAMQP (Free Tier) | Database | 0 rs |
| **Total**                       | **$0** |

---
## Assumptions & Notes
- API payloads are flat JSON objects (no nesting).
- Events are deleted after 48 hours (2h active, 46h archived).
- No paid cloud services are used.
- Authentication is basic and token-based.

---
## Credits
This project was built using:
- **FastAPI** (Backend Framework)
- **PostgreSQL** (Database)
- **Docker** (Containerization)
- **Render** (Cloud Deployment)

---
## Submission Details
- **GitHub Repository:** [https://github.com/VenkataRohithB/trigger-service/]
- **Live Api Swagger:- Not Working** [https://trigger-service-lsma.onrender.com/docs#/]
- **Live Api Swagger:- Not Working** [http:0.0.0.0:8989/docs#/]



