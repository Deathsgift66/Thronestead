# Me API

The `/api/me` endpoint returns basic details about the current authenticated user
by decoding the provided JWT.

Authentication relies on the `Authorization: Bearer <token>` header. The token is decoded using [python-jose](https://github.com/pyauth/jose) without verifying the signature. A future update will verify it using Supabase's public key.

The response is a JSON object containing:

- `user_id` – unique identifier (from the token `sub` claim)
- `email` – registered email address

Example usage:

```bash
curl -H "Authorization: Bearer <TOKEN>" \
     http://localhost:8000/api/me
```
