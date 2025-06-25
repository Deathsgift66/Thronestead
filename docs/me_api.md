# Me API

The `/api/me` endpoint returns basic details about the current authenticated user.

Authentication relies on the `Authorization: Bearer <token>` header. The token is decoded using [python-jose](https://github.com/pyauth/jose) and validated with the optional `SUPABASE_JWT_SECRET` environment variable.

The response is a JSON object containing:

- `username` – player's login handle
- `kingdom_id` – associated kingdom identifier
- `setup_complete` – boolean flag for onboarding completion

Example usage:

```bash
curl -H "Authorization: Bearer <TOKEN>" \
     http://localhost:8000/api/me
```
