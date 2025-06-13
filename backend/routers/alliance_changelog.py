from fastapi import APIRouter, Depends, HTTPException, Header

from datetime import datetime
from ..security import require_user_id


from ..supabase_client import get_supabase_client


router = APIRouter(prefix="/api/alliance/changelog", tags=["alliance_changelog"])


@router.get("")
async def get_alliance_changelog(
    since: str | None = None,
    user_id: str = Depends(require_user_id),
):
    """Return latest alliance changelog events for the player's alliance."""
    supabase = get_supabase_client()

    # Verify the requesting user exists to prevent forged headers
    user_check = (
        supabase.table("users").select("user_id").eq("user_id", user_id).single().execute()
    )
    if getattr(user_check, "error", None) or not getattr(user_check, "data", None):
        raise HTTPException(status_code=401, detail="Invalid user")

    alliance_res = (
        supabase.table("alliance_members")
        .select("alliance_id")
        .eq("user_id", user_id)
        .single()
        .execute()
    )
    alliance = getattr(alliance_res, "data", alliance_res)
    if getattr(alliance_res, "error", None) or not alliance:
        raise HTTPException(status_code=403, detail="Not in an alliance")
    alliance_id = alliance["alliance_id"]

    all_logs = []

    def add_log(source: str, entry: dict, description: str):
        all_logs.append({
            "event_type": source,
            "timestamp": entry.get("created_at") or entry.get("signed_at"),
            "actor": entry.get("user_id"),
            "description": description,
            "meta": entry,
        })

    activity = supabase.table("alliance_activity_log").select("*").eq("alliance_id", alliance_id).execute()
    for log in getattr(activity, "data", activity) or []:
        add_log("member", log, log.get("description", ""))

    treaties = (
        supabase.table("alliance_treaties")
        .select("*")
        .or_(f"alliance_id.eq.{alliance_id},partner_alliance_id.eq.{alliance_id}")
        .execute()
    )
    for t in getattr(treaties, "data", treaties) or []:
        desc = f"{t.get('treaty_type', '').title()} Treaty with Alliance {t.get('partner_alliance_id')} — Status: {t.get('status')}"
        add_log("treaty", t, desc)

    wars = (
        supabase.table("alliance_wars")
        .select("*")
        .or_(f"attacker_alliance_id.eq.{alliance_id},defender_alliance_id.eq.{alliance_id}")
        .execute()
    )
    for w in getattr(wars, "data", wars) or []:
        enemy = w["defender_alliance_id"] if w["attacker_alliance_id"] == alliance_id else w["attacker_alliance_id"]
        add_log("war", w, f"Alliance War vs {enemy}")

    projects = supabase.table("projects_alliance").select("*").eq("alliance_id", alliance_id).execute()
    for p in getattr(projects, "data", projects) or []:
        add_log("project", p, f"Project '{p.get('name')}' Status: {p.get('build_state')}")

    quests = supabase.table("quest_alliance_tracking").select("*").eq("alliance_id", alliance_id).execute()
    for q in getattr(quests, "data", quests) or []:
        add_log("quest", q, f"Quest '{q.get('quest_code')}' Progress: {q.get('progress')}")

    audits = supabase.table("audit_log").select("*").eq("user_id", user_id).execute()
    for a in getattr(audits, "data", audits) or []:
        add_log("admin", a, a.get("details", ""))

    all_logs.sort(key=lambda x: x["timestamp"], reverse=True)
    if since:
        try:
            since_dt = datetime.fromisoformat(since)
            all_logs = [l for l in all_logs if datetime.fromisoformat(l["timestamp"]) > since_dt]
        except ValueError:
            pass
    latest = all_logs[:100]

    actor_ids = [l["actor"] for l in latest if l.get("actor")]
    username_map = {}
    if actor_ids:
        user_res = (
            supabase.table("users")
            .select("user_id,username")
            .in_("user_id", actor_ids)
            .execute()
        )
        for u in getattr(user_res, "data", user_res) or []:
            username_map[u["user_id"]] = u["username"]
    for l in latest:
        uid = l.get("actor")
        if uid:
            l["actor"] = username_map.get(uid, uid)

    return latest
