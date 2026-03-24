# Auth Endpoints

These endpoints let the frontend move from client-only placeholder flows to backend-backed authentication while keeping the existing API response envelope.

## Response shape

Success responses:

```json
{
  "status": "success",
  "data": {}
}
```

Error responses:

```json
{
  "status": "error",
  "error": {
    "message": "Human-readable error",
    "details": {}
  }
}
```

## `POST /api/auth/signup`

Creates a new Supabase auth user using email/password signup.

### Request body

```json
{
  "name": "Jane Doe",
  "email": "jane@example.com",
  "password": "securepass123"
}
```

### Validation rules

- `name` is required and must be a non-empty string.
- `email` is required and must be a valid email address.
- `password` is required, must be a non-empty string, and must be at least 8 characters long.

### Success example

```json
{
  "status": "success",
  "data": {
    "user": {
      "id": "8c5044fa-6f9a-4dbf-8d1d-778603d32e13",
      "email": "jane@example.com",
      "email_confirmed_at": null,
      "last_sign_in_at": null,
      "name": "Jane Doe"
    },
    "session": {
      "access_token": "eyJhbGciOi...",
      "refresh_token": "def50200...",
      "token_type": "bearer",
      "expires_in": 3600,
      "expires_at": 1774350950
    }
  }
}
```

### Validation error example

```json
{
  "status": "error",
  "error": {
    "message": "Missing required fields",
    "details": {
      "missing": ["password"]
    }
  }
}
```

## `POST /api/auth/login`

Authenticates an existing Supabase auth user with email/password credentials.

### Request body

```json
{
  "email": "jane@example.com",
  "password": "securepass123"
}
```

### Validation rules

- `email` is required and must be a valid email address.
- `password` is required and must be a non-empty string.

### Success example

```json
{
  "status": "success",
  "data": {
    "user": {
      "id": "8c5044fa-6f9a-4dbf-8d1d-778603d32e13",
      "email": "jane@example.com",
      "email_confirmed_at": "2026-03-24T18:16:19.210695Z",
      "last_sign_in_at": "2026-03-24T18:30:05.928621Z",
      "name": "Jane Doe"
    },
    "session": {
      "access_token": "eyJhbGciOi...",
      "refresh_token": "def50200...",
      "token_type": "bearer",
      "expires_in": 3600,
      "expires_at": 1774351805
    }
  }
}
```

### Invalid credentials example

```json
{
  "status": "error",
  "error": {
    "message": "Invalid email or password",
    "details": "Invalid login credentials"
  }
}
```

## Notes for frontend integration

- Signup expects `name`, `email`, and `password`.
- Login expects `email` and `password`.
- Both endpoints return the authenticated `user` plus `session` token data when Supabase provides a session.
- If email confirmation is enabled in Supabase, signup may create the user before email verification is complete.
