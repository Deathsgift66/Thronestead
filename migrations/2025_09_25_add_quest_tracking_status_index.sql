CREATE INDEX IF NOT EXISTS idx_quest_kingdom_tracking_kingdom_status
  ON quest_kingdom_tracking (kingdom_id, status);
