# API Documentation

## Overview
This documentation provides an overview of the available API endpoints for managing users and portfolios within our system.

## Authentication
All requests to this API require a valid OAuth2 Bearer token in the `Authorization` header:
```
Authorization: Bearer <your-access-token>
```

## Base URL Configuration
The base URL for all API requests is:
```
https://api.example.com/
```

## Endpoints

### GET /api/users
**Description**
Retrieve a list of all users.

**Request Parameters**
- None

**Response Format**
```json
[
    {
        "id": "1",
        "name": "John Doe",
        "email": "john.doe@example.com"
    },
    {
        "id": "2",
        "name": "Jane Smith",
        "email": "jane.smith@example.com"
    }
]
```

**Example Request**
```bash
curl -X GET https://api.example.com/api/users \
-H 'Authorization: Bearer <your-access-token>'
```

**Example Response**
```json
[
    {
        "id": "1",
        "name": "John Doe",
        "email": "john.doe@example.com"
    },
    {
        "id": "2",
        "name": "Jane Smith",
        "email": "jane.smith@example.com"
    }
]
```

### POST /api/portfolios
**Description**
Create a new portfolio for a user.

**Request Parameters/Body**
```json
{
    "userId": "1",
    "portfolioName": "My New Portfolio",
    "initialInvestment": 5000.00
}
```

**Response Format**
```json
{
    "id": "p-1234",
    "name": "My New Portfolio",
    "ownerId": "1"
}
```

**Example Request**
```bash
curl -X POST https://api.example.com/api/portfolios \
-H 'Authorization: Bearer <your-access-token>' \
-H 'Content-Type: application/json' \
-d '{"userId":"1", "portfolioName":"My New Portfolio", "initialInvestment":5000.00}'
```

**Example Response**
```json
{
    "id": "p-1234",
    "name": "My New Portfolio",
    "ownerId": "1"
}
```

### PUT /api/portfolios/:portfolioId/rebalance
**Description**
Trigger the rebalancing of a specific portfolio.

**Request Parameters/Body**
```json
{
    "targetAllocation": [
        {"assetId":"a-001", "percentage": 50.0},
        {"assetId":"a-002", "percentage": 50.0}
    ]
}
```

**Response Format**
```json
{
    "status": "success",
    "message": "Portfolio rebalanced successfully"
}
```

**Example Request**
```bash
curl -X PUT https://api.example.com/api/portfolios/p-1234/rebalance \
-H 'Authorization: Bearer <your-access-token>' \
-H 'Content-Type: application/json' \
-d '{"targetAllocation":[{"assetId":"a-001", "percentage": 50.0}, {"assetId":"a-002", "percentage": 50.0}]}'
```

**Example Response**
```json
{
    "status": "success",
    "message": "Portfolio rebalanced successfully"
}
```

## Error Codes and Handling

| HTTP Status Code | Description |
|------------------|-------------|
| 401 Unauthorized | Invalid or missing access token. |
| 403 Forbidden    | User does not have permission to perform this action. |
| 429 Too Many Requests | Rate limit exceeded. |

## Rate Limiting Information
- Maximum requests per minute: 60
- If the rate limit is exceeded, a `429` status code will be returned with an appropriate error message.