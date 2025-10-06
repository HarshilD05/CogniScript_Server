# User Management APIs Documentation

Comprehensive documentation for user creation, retrieval, and management operations.

**Base URL:** `{serverURL}/api`
- **Local Development:** `http://localhost:5000/api`
- **Production:** `https://your-domain.com/api`

---

## User Creation & Management

### 1. Create User
**`POST {serverURL}/api/users`**

Create a new user in the system.

**Request Body:**
```json
{
  "email": "string (required)",
  "user_type": "string (required)"
}
```

**Response (201):**
```json
{
  "message": "User created successfully",
  "user_id": "string",
  "email": "string",
  "user_type": "string"
}
```

**Example:**
```bash
curl -X POST http://localhost:5000/api/users \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "user_type": "standard"
  }'
```

**Error Responses:**
- `409 Conflict` - User with email already exists
- `400 Bad Request` - Missing required fields or validation error

---

## User Retrieval

### 2. Get User by ID
**`GET {serverURL}/api/users/{user_id}`**

Retrieve a specific user by their ID.

**Path Parameters:**
- `user_id`: MongoDB ObjectId of the user

**Response (200):**
```json
{
  "message": "User retrieved successfully",
  "user": {
    "user_id": "string",
    "email": "string",
    "user_type": "string",
    "chats": ["array of chat IDs"],
    "created_at": "string",
    "updated_at": "string"
  }
}
```

**Example:**
```bash
curl -X GET http://localhost:5000/api/users/64a7b1234567890123456789
```

### 3. Get User by Email
**`GET {serverURL}/api/users/email/{email}`**

Retrieve a user by their email address.

**Path Parameters:**
- `email`: Email address of the user

**Response (200):**
```json
{
  "message": "User retrieved successfully",
  "user": {
    "user_id": "string",
    "email": "string",
    "user_type": "string",
    "chats": ["array"],
    "created_at": "string",
    "updated_at": "string"
  }
}
```

**Example:**
```bash
curl -X GET http://localhost:5000/api/users/email/user@example.com
```

---

## User Chat Management

### 4. Get User Chats
**`GET {serverURL}/api/users/{user_id}/chats?limit=50&skip=0`**

Get all chats for a specific user with pagination.

**Path Parameters:**
- `user_id`: MongoDB ObjectId of the user

**Query Parameters:**
- `limit`: number (optional, max 100, default: 50)
- `skip`: number (optional, default: 0)

**Response (200):**
```json
{
  "message": "User chats retrieved successfully",
  "user_id": "string",
  "chats": ["array of chat objects"],
  "count": "number",
  "limit": "number",
  "skip": "number"
}
```

**Example:**
```bash
curl -X GET "http://localhost:5000/api/users/64a7b1234567890123456789/chats?limit=10&skip=0"
```

---

## System Monitoring

### 5. User Health Check
**`GET {serverURL}/api/users/health`**

Health check endpoint for user APIs.

**Response (200):**
```json
{
  "status": "healthy",
  "service": "user_apis",
  "endpoints": ["array of available endpoints"]
}
```

**Example:**
```bash
curl -X GET http://localhost:5000/api/users/health
```

---

## User Types

The system supports different user types:
- **`standard`** - Regular user with full access
- **`admin`** - Administrative privileges (if implemented)
- **`trial`** - Limited access user (if implemented)

---

## User Workflow

1. **Create User:** Register with email and user_type
2. **Create Chats:** Use user_id to create chat sessions
3. **Manage Chats:** View all chats associated with the user
4. **Retrieve User:** Get user details by ID or email

---

## Data Models

### User Object
```json
{
  "_id": "MongoDB ObjectId",
  "email": "string (unique)",
  "user_type": "string",
  "chats": ["array of chat ObjectIds"],
  "created_at": "ISO 8601 datetime",
  "updated_at": "ISO 8601 datetime"
}
```

### Chat Reference
When a chat is created, the chat ID is automatically added to the user's `chats` array for tracking purposes.

---

## Error Responses

All endpoints may return these common error responses:

**400 Bad Request:**
```json
{
  "error": "email and user_type are required"
}
```

**404 Not Found:**
```json
{
  "error": "User not found"
}
```

**409 Conflict:**
```json
{
  "error": "User with this email already exists"
}
```

**500 Internal Server Error:**
```json
{
  "error": "Internal server error"
}
```

---

## Validation Rules

- **Email:** Must be a valid email format
- **User Type:** Required string field
- **User ID:** Must be a valid MongoDB ObjectId (24-character hex string)

---

## Integration with Chat System

Users are tightly integrated with the chat system:
- Creating a chat requires a valid `userId`
- Users automatically track their associated chats
- Deleting a chat updates the user's chat list
- Chat permissions are based on user ownership

---

*Last updated: October 6, 2025*