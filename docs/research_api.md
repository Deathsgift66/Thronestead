# Research API

The `/api/kingdom/research` endpoint returns all research projects for the
authenticated user's kingdom.

## Query Parameters

- `category` *(optional)* – filter results to a specific technology category.

Example request:

```bash
curl -H "Authorization: Bearer <TOKEN>" \
     http://localhost:8000/api/kingdom/research?category=economic
```

The response is a JSON object containing a `research` array with each entry's
`tech_code`, `status`, `progress` and `ends_at` fields.

