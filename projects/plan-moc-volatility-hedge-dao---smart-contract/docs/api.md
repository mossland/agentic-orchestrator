# API Documentation

## Overview

This documentation provides detailed information about our RESTful API, which allows users to manage their insurance policies and trades.

## Authentication

To use this API, you must include an `Authorization` header in your requests with a JWT (JSON Web Token) obtained from our authentication service. The token should be passed as follows:

```
Authorization: Bearer <your_token>
```

## Base URL Configuration

All endpoints are prefixed by the base URL:
```
https://api.example.com
```

## API Endpoints

### GET /api/users/{userId}/insurance-policies

#### Description
Retrieve all insurance policies for a specific user.

#### Request Parameters
- `userId`: The unique identifier of the user whose insurance policies you want to retrieve. This parameter is required and must be included in the URL path.

#### Response Format
A JSON array containing objects with details about each policy:
```json
[
  {
    "policyId": "string",
    "coverageType": "string",
    "amountCovered": "number",
    "startDate": "date",
    "endDate": "date"
  },
  ...
]
```

#### Example Request
```http
GET /api/users/1234567890/insurance-policies HTTP/1.1
Host: api.example.com
Authorization: Bearer <your_token>
```

#### Example Response
```json
[
  {
    "policyId": "p-123",
    "coverageType": "Health",
    "amountCovered": 50000,
    "startDate": "2023-01-01",
    "endDate": "2024-01-01"
  },
  ...
]
```

### POST /api/users/{userId}/insurance-policies

#### Description
Purchase a new insurance policy for the user.

#### Request Parameters/Body
The request body should contain details about the new policy:
```json
{
  "coverageType": "string",
  "amountCovered": "number",
  "startDate": "date",
  "endDate": "date"
}
```

#### Response Format
A JSON object with a confirmation message and the newly created policy ID:
```json
{
  "message": "Policy successfully purchased.",
  "policyId": "string"
}
```

#### Example Request
```http
POST /api/users/1234567890/insurance-policies HTTP/1.1
Host: api.example.com
Authorization: Bearer <your_token>
Content-Type: application/json

{
  "coverageType": "Auto",
  "amountCovered": 10000,
  "startDate": "2023-06-01",
  "endDate": "2024-05-31"
}
```

#### Example Response
```json
{
  "message": "Policy successfully purchased.",
  "policyId": "p-123456789"
}
```

### GET /api/users/{userId}/trades

#### Description
Retrieve all trades for a specific user.

#### Request Parameters
- `userId`: The unique identifier of the user whose trades you want to retrieve. This parameter is required and must be included in the URL path.

#### Response Format
A JSON array containing objects with details about each trade:
```json
[
  {
    "tradeId": "string",
    "type": "Buy" | "Sell",
    "amount": "number",
    "pricePerUnit": "number",
    "dateExecuted": "date"
  },
  ...
]
```

#### Example Request
```http
GET /api/users/1234567890/trades HTTP/1.1
Host: api.example.com
Authorization: Bearer <your_token>
```

#### Example Response
```json
[
  {
    "tradeId": "t-123",
    "type": "Buy",
    "amount": 10,
    "pricePerUnit": 50.75,
    "dateExecuted": "2023-04-01"
  },
  ...
]
```

## Error Codes and Handling

| HTTP Status Code | Description                     |
|------------------|---------------------------------|
| 400              | Bad Request, usually a malformed request body or missing required parameters. |
| 401              | Unauthorized, invalid or expired token. |
| 403              | Forbidden, the user does not have permission to access this resource. |
| 404              | Not Found, the requested resource could not be found. |
| 500              | Internal Server Error, something went wrong on our end. |

## Rate Limiting

The API has a rate limit of 100 requests per minute per user token. If you exceed this limit, your IP address will be temporarily blocked from making further requests.

---

This documentation is subject to updates and changes as the service evolves.