# ⚙️ Redis Caching for Thronestead

## Use Cases
- Modifier stacks per kingdom
- Current tick phase state
- Recently completed quests
- Treaty expiration watches
- War tick deltas

## TTL Strategy
| Data                | TTL      | Key Format                       |
|---------------------|----------|----------------------------------|
| Modifier Stack      | 60s      | `modifiers:kingdom:<id>`         |
| Quest Status        | 120s     | `quests:<kingdom_id>`            |
| War Phase           | 10s      | `war:phase:<war_id>`             |

## Redis Command Example
```python
r.set(f"modifiers:kingdom:{kingdom_id}", json.dumps(result), ex=60)
```

## Invalidation
- On project/research/war tick
- On treaty change