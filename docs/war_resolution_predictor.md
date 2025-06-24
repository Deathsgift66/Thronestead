# 📉 Battle Score Curve & Resolution Prediction

Provides a pre-resolution predictor and post-resolution analyzer based on combat logs.
Changes to `combat_logs` are automatically written to `audit_log` via trigger `trg_combat_logs_audit`.

## Inputs
- `combat_logs` (ticks 0 → N)
- `unit_stats` (base power)
- `castle_hp`, `morale`, `casualties`, `score_diff`

## Visualization
**Sample Curve (War ID 42)**

- 🟥 Red = Defender score
- 🟦 Blue = Attacker score

```
[Tick] A:Score D:Score Castle HP  Notes
  0     0        0        10000   Battle Start
  1    25       18        9750    First engagement
  2    80       30        9000    Siege wave 1
  3   105       90        8500    Mid-skirmish
  4   150      145        8100    Deadlock
```

### Outcome
🧠 Model Projects: Victory Likely → **Attacker Wins in 2 More Ticks**