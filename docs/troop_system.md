# Troop System Overview

Thronestead categorizes units by tactical roles. Two special flags influence combat resolution:

- **`is_support`** – Units that provide healing and morale boosts to allies on the same tile each tick.
- **`is_siege`** – Units that inflict direct damage to the enemy castle during the siege phase of a tick.

Support units restore a small amount of health and morale before combat is calculated. Multiple support stacks will stack their effect. Siege units contribute to castle damage at the end of each tick, reducing the enemy stronghold even if no defenders are present.

These roles appear in the training queue and help players plan their formations effectively.
