# Progression API Curl Examples

## Castle Progression
```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{"xp_gain": 50}' \
  http://localhost:8000/api/progression/castle/progress
```

## Nobles Management
### Add Noble
```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{"name": "Arthur"}' \
  http://localhost:8000/api/progression/nobles
```

### Remove Noble
```bash
curl -X DELETE http://localhost:8000/api/progression/nobles/Arthur
```

## Knights Management
### Add Knight
```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{"id": "k1", "rank": 1}' \
  http://localhost:8000/api/progression/knights
```

### Promote Knight
```bash
curl -X POST http://localhost:8000/api/progression/knights/k1/promote
```
