# Project Name: Thronestead©
# File Name: alliance_changelog.py
# Version: 6.13.2025.19.49
# Developer: Deathsgift66

from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime
from typing import Optional

from ..security import require_user_id
from ..supabase_client import get_supabase_client

router = APIRouter(prefix="/api/alliance/changelog", tags=["alliance_changelog"])


@router.get("")
def get_alliance_changelog(
    since: Optional[str] = None,
    user_id: str = Depends(require_user_id),
):
    """
    Return the latest alliance changelog events for the requesting user's alliance.
    This includes alliance activity, treaties, wars, projects, quests, and audit log actions.
    """
    supabase = get_supabase_client()

    # ✅ Validate user existence to prevent forged headers
    user_check = supabase.table("users").select("user_id").eq("user_id", user_id).single().execute()
    if getattr(user_check, "error", None) or not getattr(user_check, "data", None):
        raise HTTPException(status_code=401, detail="Invalid user")

    # ✅ Fetch the user's alliance membership
    alliance_res = supabase.table("alliance_members").select("alliance_id").eq("user_id", user_id).single().execute()
    if getattr(alliance_res, "error", None) or not getattr(alliance_res, "data", None):
        raise HTTPException(status_code=403, detail="User is not in an alliance")
    
    alliance_id = alliance_res.data["alliance_id"]
    all_logs = []

    def add_log(source: str, entry: dict, description: str):
        """Append a formatted log entry to the master log list."""
        all_logs.append({
            "event_type": source,
            "timestamp": entry.get("created_at") or entry.get("signed_at"),
            "actor": entry.get("user_id"),
            "description": description,
            "meta": entry,
        })

    # 🧾 1. Activity Log
    activity = supabase.table("alliance_activity_log").select("*").eq("alliance_id", alliance_id).execute()
    for log in getattr(activity, "data", []):
        add_log("member", log, log.get("description", ""))

    # 📜 2. Treaties
    treaties = supabase.table("alliance_treaties") \
        .select("*") \
        .or_(f"alliance_id.eq.{alliance_id},partner_alliance_id.eq.{alliance_id}") \
        .execute()
    for t in getattr(treaties, "data", []):
        desc = f"{t.get('treaty_type', '').title()} Treaty with Alliance {t.get('partner_alliance_id')} — Status: {t.get('status')}"
        add_log("treaty", t, desc)

    # ⚔️ 3. Wars
    wars = supabase.table("alliance_wars") \
        .select("*") \
        .or_(f"attacker_alliance_id.eq.{alliance_id},defender_alliance_id.eq.{alliance_id}") \
        .execute()
    for w in getattr(wars, "data", []):
        enemy_id = w["defender_alliance_id"] if w["attacker_alliance_id"] == alliance_id else w["attacker_alliance_id"]
        add_log("war", w, f"Alliance War vs Alliance {enemy_id}")

    # 🏗️ 4. Projects
    projects = supabase.table("projects_alliance").select("*").eq("alliance_id", alliance_id).execute()
    for p in getattr(projects, "data", []):
        add_log("project", p, f"Project '{p.get('name')}' Status: {p.get('build_state')}")

    # 📘 5. Quests
    quests = supabase.table("quest_alliance_tracking").select("*").eq("alliance_id", alliance_id).execute()
    for q in getattr(quests, "data", []):
        add_log("quest", q, f"Quest '{q.get('quest_code')}' Progress: {q.get('progress')}%")

    # 🛡️ 6. Audit Logs
    audits = supabase.table("audit_log").select("*").eq("user_id", user_id).execute()
    for a in getattr(audits, "data", []):
        add_log("admin", a, a.get("details", ""))

    # 🕓 Sort and Filter Logs
    all_logs = [log for log in all_logs if log.get("timestamp")]
    all_logs.sort(key=lambda x: x["timestamp"], reverse=True)

    if since:
        try:
            since_dt = datetime.fromisoformat(since)
            all_logs = [log for log in all_logs if datetime.fromisoformat(log["timestamp"]) > since_dt]
        except ValueError:
            pass  # ignore filter if date is malformed

    latest_logs = all_logs[:100]

    # 👤 Resolve actor names
    actor_ids = list({log["actor"] for log in latest_logs if log.get("actor")})
    username_map = {}

    if actor_ids:
        user_res = supabase.table("users") \
            .select("user_id,username") \
            .in_("user_id", actor_ids) \
            .execute()
        for u in getattr(user_res, "data", []):
            username_map[u["user_id"]] = u["username"]

    for log in latest_logs:
        actor_id = log.get("actor")
        if actor_id:
            log["actor"] = username_map.get(actor_id, actor_id)

    return latest_logs
