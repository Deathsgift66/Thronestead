# Progression API Curl Examples

## Get Castle Level
```bash
curl -H "X-User-Id: <USER>" http://localhost:8000/api/progression/castle
```

## Upgrade Castle
```bash
curl -X POST -H "X-User-Id: <USER>" http://localhost:8000/api/progression/castle
```

## List Nobles
```bash
curl -H "X-User-Id: <USER>" http://localhost:8000/api/progression/nobles
```

## Assign Noble
```bash
curl -X POST -H "X-User-Id: <USER>" \
     -H "Content-Type: application/json" \
     -d '{"noble_name": "Arthur"}' \
     http://localhost:8000/api/progression/nobles
```

## List Knights
```bash
curl -H "X-User-Id: <USER>" http://localhost:8000/api/progression/knights
```

## Assign Knight
```bash
curl -X POST -H "X-User-Id: <USER>" \
     -H "Content-Type: application/json" \
     -d '{"knight_name": "Lancelot"}' \
     http://localhost:8000/api/progression/knights
```

## Refresh Totals
```bash
curl -X POST -H "X-User-Id: <USER>" http://localhost:8000/api/progression/refresh
```
