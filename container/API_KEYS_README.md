# API Key Management System

This document describes the API key management system implemented in the application.

## Overview

The API key management system allows users to create, manage, and use API keys for authentication. API keys provide an alternative to JWT tokens for programmatic access to the API.

## Features

- **Secure API Key Generation**: API keys are cryptographically secure and prefixed with `pk_`
- **Hashed Storage**: API keys are hashed before storage for security
- **Permission System**: Each API key can have specific permissions assigned
- **Expiration Support**: API keys can have optional expiration dates
- **Status Management**: API keys can be active, inactive, expired, or revoked
- **Usage Tracking**: Last used timestamps are automatically updated
- **User Isolation**: Users can only manage their own API keys

## API Endpoints

### Create API Key
```
POST /api/v1/api-keys
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "name": "My API Key",
  "description": "Optional description",
  "permissions": ["read", "write"],
  "expires_at": "2024-12-31T23:59:59Z"  // Optional
}
```

**Response:**
```json
{
  "id": "uuid",
  "name": "My API Key",
  "api_key": "pk_abc123...",  // Only returned once
  "description": "Optional description",
  "permissions": ["read", "write"],
  "status": "active",
  "created_at": "2024-01-01T00:00:00Z",
  "expires_at": "2024-12-31T23:59:59Z"
}
```

### List API Keys
```
GET /api/v1/api-keys?limit=10&offset=0
Authorization: Bearer <jwt_token>
```

**Response:**
```json
{
  "api_keys": [
    {
      "uuid": "uuid",
      "name": "My API Key",
      "description": "Optional description",
      "status": "active",
      "permissions": ["read", "write"],
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T00:00:00Z",
      "expires_at": "2024-12-31T23:59:59Z",
      "last_used_at": "2024-01-01T12:00:00Z"
    }
  ]
}
```

### Get API Key
```
GET /api/v1/api-keys/<api_key_id>
Authorization: Bearer <jwt_token>
```

### Update API Key
```
PUT /api/v1/api-keys/<api_key_id>
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "name": "Updated Name",
  "description": "Updated description",
  "permissions": ["read"],
  "status": "inactive",
  "expires_at": "2024-12-31T23:59:59Z"
}
```

### Delete API Key
```
DELETE /api/v1/api-keys/<api_key_id>
Authorization: Bearer <jwt_token>
```

### Revoke API Key
```
POST /api/v1/api-keys/<api_key_id>/revoke
Authorization: Bearer <jwt_token>
```

## Using API Keys for Authentication

API keys can be used as an alternative to JWT tokens for authentication. Simply include the API key in the Authorization header:

```
Authorization: pk_your_api_key_here
```

The system will automatically detect API keys (they start with `pk_`) and validate them accordingly.

## Permission System

### Available Permissions

- `read`: Read access to resources
- `write`: Write access to resources
- `admin`: Administrative access
- `chat`: Access to chat functionality
- `agents`: Access to agent management
- `documents`: Access to document management
- `files`: Access to file management

### Using Permissions

You can use the permission decorators in your controllers:

```python
from utils.permission_utils import require_permission, require_any_permission

@app.route('/api/v1/protected-endpoint', methods=['GET'])
@login_required
@require_permission('read')
def protected_endpoint():
    return jsonify({"message": "Access granted"})

@app.route('/api/v1/admin-endpoint', methods=['POST'])
@login_required
@require_any_permission(['admin', 'write'])
def admin_endpoint():
    return jsonify({"message": "Admin access granted"})
```

## Security Features

1. **Cryptographic Security**: API keys are generated using `secrets.token_urlsafe()`
2. **Hashed Storage**: API keys are hashed using SHA-256 before storage
3. **Secure Comparison**: Uses `hmac.compare_digest()` for timing-attack-resistant comparison
4. **Automatic Expiration**: Expired keys are automatically marked as expired
5. **Status Tracking**: Keys can be active, inactive, expired, or revoked
6. **Usage Tracking**: Last used timestamps are automatically updated

## Database Schema

The API keys are stored in the `ApiKeys` collection with the following properties:

- `name`: Human-readable name for the API key
- `description`: Optional description
- `key_hash`: SHA-256 hash of the API key
- `user_id`: ID of the user who owns the key
- `status`: Current status (active, inactive, expired, revoked)
- `permissions`: JSON array of permissions
- `created_at`: Creation timestamp
- `updated_at`: Last update timestamp
- `expires_at`: Optional expiration timestamp
- `last_used_at`: Last usage timestamp

## Best Practices

1. **Store API Keys Securely**: Never store API keys in plain text
2. **Use Descriptive Names**: Give API keys meaningful names for easy identification
3. **Set Expiration Dates**: Always set expiration dates for API keys
4. **Limit Permissions**: Only grant the minimum necessary permissions
5. **Monitor Usage**: Regularly check last used timestamps
6. **Rotate Keys**: Periodically rotate API keys for security
7. **Revoke Unused Keys**: Delete or revoke unused API keys

## Error Handling

The API returns appropriate HTTP status codes:

- `200`: Success
- `201`: Created
- `400`: Bad Request (missing required fields)
- `401`: Unauthorized (invalid API key)
- `403`: Forbidden (insufficient permissions)
- `404`: Not Found (API key not found)
- `500`: Internal Server Error

## Example Usage

### Creating an API Key
```bash
curl -X POST http://localhost:5000/api/v1/api-keys \
  -H "Authorization: Bearer your_jwt_token" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Application",
    "description": "API key for my application",
    "permissions": ["read", "write"],
    "expires_at": "2024-12-31T23:59:59Z"
  }'
```

### Using an API Key
```bash
curl -X GET http://localhost:5000/api/v1/protected-endpoint \
  -H "Authorization: pk_your_api_key_here"
```

## Migration Notes

If you're upgrading from a previous version:

1. The API keys collection will be automatically created when the application starts
2. Existing JWT authentication will continue to work
3. API key authentication is backward compatible
4. No data migration is required 