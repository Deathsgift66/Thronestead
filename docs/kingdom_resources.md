# Kingdom Resources

The `kingdom_resources` table stores the on-hand stockpile for a player's kingdom. It acts as the "resource wallet" where all produced materials are deposited and from which costs are deducted.

## Table Structure

| Column | Meaning |
| --- | --- |
| `kingdom_id` | Which kingdom this row belongs to. Primary key. |
| `wood` | Amount of wood. |
| `stone` | Amount of stone. |
| `iron_ore` | Amount of iron ore. |
| `gold` | Amount of gold. |
| `gems` | Amount of gems. |
| `food` | Food supply. |
| `coal` | Coal supply. |
| `livestock` | Livestock. |
| `clay` | Clay. |
| `flax` | Flax. |
| `tools` | Tools. |
| `wood_planks` | Wood planks. |
| `refined_stone` | Refined stone. |
| `iron_ingots` | Iron ingots. |
| `charcoal` | Charcoal. |
| `leather` | Leather. |
| `arrows` | Arrows. |
| `swords` | Swords. |
| `axes` | Axes. |
| `shields` | Shields. |
| `armor` | Armor. |
| `wagon` | Wagons. |
| `siege_weapons` | Siege weapons. |
| `jewelry` | Jewelry. |
| `spear` | Spears. |
| `horses` | Horses. |
| `pitchforks` | Pitchforks. |

## Usage

### Showing resources in the UI
Query the row for the player's kingdom and display each column on the various economy screens.

```sql
SELECT *
FROM public.kingdom_resources
WHERE kingdom_id = 5;
```

### Producing resources
Add hourly or event production amounts to the row.

```sql
UPDATE public.kingdom_resources
SET wood = wood + 100,
    stone = stone + 50,
    food = food + 200
WHERE kingdom_id = 5;
```

### Spending resources
Always check the current values first and ensure they do not go negative when deducting costs.

```sql
SELECT wood, stone
FROM public.kingdom_resources
WHERE kingdom_id = 5;

UPDATE public.kingdom_resources
SET wood = wood - 100,
    stone = stone - 50
WHERE kingdom_id = 5;
```

### Taxes, trades and war loot
Alliance taxes withdraw from this table and deposit into `alliance_vault`. Trades and war loot transfer amounts between kingdoms by updating each kingdom's row.

## Best Practices

* Only one row exists per kingdom – use `kingdom_id` as the primary key.
* Use `SELECT ... FOR UPDATE` when performing critical resource updates to avoid race conditions.
* Prevent negative values in application logic or with check constraints.
* Consider logging transactions in a separate `kingdom_resource_transaction_log` table for auditing.

### Programmatic Updates

The backend exposes helper functions in
[`services/resource_service.py`](../services/resource_service.py) for common
operations:

- `spend_resources(db, kingdom_id, cost)` deducts resources safely and raises
  an error if funds are insufficient.
- `gain_resources(db, kingdom_id, gain)` credits new resources to the kingdom.
- `get_kingdom_resources(db, kingdom_id, lock=False)` fetches the current
  ledger. Pass ``lock=True`` to acquire a `FOR UPDATE` lock for atomic updates.

Use these helpers when implementing features that modify `kingdom_resources` to
ensure consistent logging and validation.
