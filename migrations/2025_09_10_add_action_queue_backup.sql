CREATE TABLE IF NOT EXISTS action_queue_backup (
    backup_id SERIAL PRIMARY KEY,
    source_table text NOT NULL,
    row_data jsonb NOT NULL,
    inserted_at timestamp with time zone DEFAULT now()
);

CREATE OR REPLACE FUNCTION log_action_queue_backup()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO action_queue_backup (source_table, row_data)
    VALUES (TG_TABLE_NAME, to_jsonb(NEW));
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_projects_alliance_backup
AFTER INSERT ON projects_alliance
FOR EACH ROW EXECUTE FUNCTION log_action_queue_backup();

CREATE TRIGGER trg_projects_alliance_in_progress_backup
AFTER INSERT ON projects_alliance_in_progress
FOR EACH ROW EXECUTE FUNCTION log_action_queue_backup();

CREATE TRIGGER trg_projects_player_backup
AFTER INSERT ON projects_player
FOR EACH ROW EXECUTE FUNCTION log_action_queue_backup();

CREATE TRIGGER trg_quest_alliance_tracking_backup
AFTER INSERT ON quest_alliance_tracking
FOR EACH ROW EXECUTE FUNCTION log_action_queue_backup();

CREATE TRIGGER trg_quest_kingdom_tracking_backup
AFTER INSERT ON quest_kingdom_tracking
FOR EACH ROW EXECUTE FUNCTION log_action_queue_backup();

CREATE TRIGGER trg_alliance_votes_backup
AFTER INSERT ON alliance_votes
FOR EACH ROW EXECUTE FUNCTION log_action_queue_backup();
