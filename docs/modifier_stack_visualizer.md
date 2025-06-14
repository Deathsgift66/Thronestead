# 🧠 Modifier Stack Visualizer

This document outlines how modifiers are layered and resolved for any game entity.

## Sources of Modifiers
- 🔍 Region: `region_bonuses`
- 🧪 Research: `tech_catalogue → modifiers`
- 🏗 Projects: `project_modifiers`
- 🛡 Treaties: `treaty_modifiers`
- 🏘 Villages: `village_modifiers`

## Example Stack (Kingdom 42, Resource: `wood`)
| Source           | Type     | Target       | Magnitude | Finalized |
|------------------|----------|--------------|-----------|-----------|
| Region: Forest   | flat     | wood_output  | +10%      | ✔         |
| Research: Forestry I | percent  | wood_output  | +5%       | ✔         |
| Project: Wood Trust | percent | wood_output  | +15%      | ✔         |
| Treaty: Resource Pact | flat | wood_output  | +20       | ✔         |
| **TOTAL EFFECT** |          |              | **+30% +20** |           |