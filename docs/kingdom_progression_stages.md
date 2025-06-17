# Kingdom Progression Stages

This document summarizes the staged progression design for Thronestead. The features described here are implemented across the backend services and client pages. The progression system ensures that players unlock new mechanics at predictable milestones.

## Stage 1: Initial Kingdom Setup
- **Account Creation** – Player starts with a level 1 castle, one village and one noble. Knights are not yet available.
- **Early Quests** – Direct the player to upgrade their starting village and recruit basic troops.
- **Unlocked Content** – Base troop slots and initial resource production.

## Stage 2: Castle Progression Begins
- **Castle Level 2** – Grants a second noble, increases the maximum villages and awards additional troop slots.
- **Second Village** – The new noble can found and specialize an additional village.
- **Kingdom Quests** – Encourage economic growth and the start of a military build up. Alliance membership becomes possible.

## Stage 3: Alliance Join & Projects
- **Alliance Membership** – Enables contribution to alliance projects, alliance quests and access to the alliance vault.
- **Further Progression** – Nobles and knights are earned through castle upgrades, projects and quest rewards.

## Stage 4: Military & Diplomacy
- **Castle Levels 3–4** – Unlock knights and advanced troop tiers. Knights can be assigned to armies.
- **War & Treaties** – Players can start wars and propose treaties once they have enough nobles and knights.

## Stage 5: Advanced Kingdom Management
- **Castle Level 5+** – Large kingdoms with many villages become possible. Nobles are required for major projects, declarations of war and high‑tier diplomacy. Knights lead armies and provide military bonuses.
- **Strategic Balance** – Players must manage village specialization, noble allocation and knight progression.

## Stage 6: Global Scale Gameplay
- **Large Scale Wars** – Alliance wars and global projects open up. Prestige now reflects player activity only. Ranking continues to depend on castle level, military success, alliance achievements and economic power.

## High Level Game Loops
- **Primary Loop** – `Castle Level → Nobles → Villages → Resources → Troops → Wars → Castle Level ↑`
- **Military Loop** – `Castle Level → Knights → Troop Slots → Elite Troops → War Participation → Military Rank ↑`
- **Alliance Loop** – `Alliance Membership → Alliance Quests → Alliance Projects → Alliance Wars → Global Rank ↑`
- **Diplomacy Loop** – `Nobles → Treaties → War Alliances → Global Politics → Reputation ↑`

These loops help structure the overall gameplay experience and inform how new features should be integrated into the existing codebase.
