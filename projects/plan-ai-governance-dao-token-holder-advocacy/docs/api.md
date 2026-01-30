# API Documentation

## Overview
This document provides comprehensive information on how to interact with our RESTful API endpoints for user retrieval and audit log creation.

## Authentication
All API requests require an `Authorization` header containing a Bearer token, which is obtained after successful authentication via OAuth 2.0 or similar mechanisms.

## Base URL Configuration
Base URL: https://api.example.com/

## Endpoints

### GET /api/users
#### Description
Retrieve a list of users from the system.

#### Request Parameters
- `page` (optional): Integer indicating the page number for pagination.
- `limit` (optional): Integer specifying the number of results per page. Default is 10.

#### Response Format
```json
{
    "users": [
        {
            "id": 1,
            "name": "John Doe",
            "email": "john.doe@example.com"
        },
        ...
    ],
    "total_pages": 5,
    "current_page": 1
}
```

#### Example Request
```http
GET /api/users?page=2&limit=10 HTTP/1.1
Host: api.example.com
Authorization: Bearer <access_token>
```

#### Example Response
```json
{
    "users": [
        {
            "id": 11,
            "name": "Jane Doe",
            "email": "jane.doe@example.com"
        },
        ...
    ],
    "total_pages": 5,
    "current_page": 2
}
```

### POST /api/audit-logs
#### Description
Create an audit log entry in the system.

#### Request Body
```json
{
    "action": "login",
    "user_id": 1,
    "details": {
        "ip_address": "192.0.2.1"
    }
}
```

#### Response Format
```json
{
    "status": "success",
    "message": "Audit log created successfully."
}
```

#### Example Request
```http
POST /api/audit-logs HTTP/1.1
Host: api.example.com
Authorization: Bearer <access_token>
Content-Type: application/json

{
    "action": "login",
    "user_id": 1,
    "details": {
        "ip_address": "192.0.2.1"
    }
}
```

#### Example Response
```json
{
    "status": "success",
    "message": "Audit log created successfully."
}
```

## Error Codes and Handling

| HTTP Status Code | Description |
|------------------|-------------|
| 400              | Bad Request - The request was invalid or cannot be served. |
| 401              | Unauthorized - No valid API key provided. |
| 403              | Forbidden - The server understood the request but refuses to authorize it. |
| 500              | Internal Server Error - An unexpected condition occurred on the server side. |

## Rate Limiting Information
The API enforces a rate limit of 100 requests per minute for each authenticated user.

Exceeding this limit will result in HTTP status code `429 Too Many Requests`.