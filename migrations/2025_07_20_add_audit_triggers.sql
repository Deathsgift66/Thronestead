-- Audit triggers for wars, combat_logs, and training_history

-- Generic trigger function to log changes
CREATE OR REPLACE FUNCTION log_table_change()
RETURNS TRIGGER AS $$
DECLARE
    detail text;
    uid uuid;
    kid integer;
BEGIN
    IF TG_TABLE_NAME = 'wars' THEN
        uid := COALESCE(NEW.submitted_by, OLD.submitted_by);
        kid := COALESCE(NEW.attacker_kingdom_id, OLD.attacker_kingdom_id);
        IF TG_OP = 'DELETE' THEN
            detail := 'wars delete id=' || OLD.war_id;
        ELSIF TG_OP = 'UPDATE' THEN
            detail := 'wars update id=' || NEW.war_id;
        ELSE
            detail := 'wars insert id=' || NEW.war_id;
        END IF;

    ELSIF TG_TABLE_NAME = 'combat_logs' THEN
        uid := NULL;
        kid := NULL;
        IF TG_OP = 'DELETE' THEN
            detail := 'combat_logs delete id=' || OLD.combat_id;
        ELSIF TG_OP = 'UPDATE' THEN
            detail := 'combat_logs update id=' || NEW.combat_id;
        ELSE
            detail := 'combat_logs insert id=' || NEW.combat_id;
        END IF;

    ELSIF TG_TABLE_NAME = 'training_history' THEN
        uid := COALESCE(NEW.trained_by, OLD.trained_by);
        kid := COALESCE(NEW.kingdom_id, OLD.kingdom_id);
        IF TG_OP = 'DELETE' THEN
            detail := 'training_history delete id=' || OLD.history_id;
        ELSIF TG_OP = 'UPDATE' THEN
            detail := 'training_history update id=' || NEW.history_id;
        ELSE
            detail := 'training_history insert id=' || NEW.history_id;
        END IF;
    END IF;

    INSERT INTO audit_log(user_id, action, details, kingdom_id)
    VALUES (uid, TG_TABLE_NAME || '_' || lower(TG_OP), detail, kid);

    IF TG_OP = 'DELETE' THEN
        RETURN OLD;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Attach triggers to tables
CREATE TRIGGER trg_wars_audit
AFTER INSERT OR UPDATE OR DELETE ON wars
FOR EACH ROW EXECUTE FUNCTION log_table_change();

CREATE TRIGGER trg_combat_logs_audit
AFTER INSERT OR UPDATE OR DELETE ON combat_logs
FOR EACH ROW EXECUTE FUNCTION log_table_change();

CREATE TRIGGER trg_training_history_audit
AFTER INSERT OR UPDATE OR DELETE ON training_history
FOR EACH ROW EXECUTE FUNCTION log_table_change();
