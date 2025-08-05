// Consolidated kingdom modules
// This file aggregates various kingdom-related scripts for convenience.

// Side-effect imports - these modules self-initialize on DOMContentLoaded
import './edit_kingdom.js';
import './kingdom_history.js';
import './villages.js';
import './village_master.js';
import './unlocked_troops.js';

// Re-export functions from modules that provide them
export { initProjectsPage } from './projects_kingdom.js';
export { initAchievementsPage } from './kingdom_achievements.js';
export { applyKingdomLinks } from './kingdom_name_linkify.js';
