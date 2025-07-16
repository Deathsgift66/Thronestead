// Shared constants for Thronestead
export const RANK_POWER = ['Member', 'Diplomat', 'War Officer', 'Co-Leader', 'Leader'];
export const RANK_POWER_NORMALIZED = RANK_POWER.map(r => r.toLowerCase());
export const rankLevel = r => RANK_POWER_NORMALIZED.indexOf((r || 'member').toLowerCase());
