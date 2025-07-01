# Comment
# Project Name: Thronestead©
# File Name: modifier_stack_service.py
# Version: 7/1/2025 10:31
# Developer: Deathsgift66

"""Central logic for computing, tracing, and summarizing active kingdom modifiers."""

from __future__ import annotations

import json
import logging

try:
    from sqlalchemy import text
    from sqlalchemy.orm import Session
except ImportError:

    def text(q):  # type: ignore
        return q

    Session = object  # type: ignore


def _merge_stack(stack: dict, modifiers: dict, source: str) -> None:
    """Merge new modifiers into a categorized stack with their sources."""
    if not isinstance(modifiers, dict):
        return

    for category, values in modifiers.items():
        if not isinstance(values, dict):
            continue
        cat_entry = stack.setdefault(category, {})
        for key, val in values.items():
            item = cat_entry.setdefault(key, {"total": 0, "sources": []})
            item["total"] += val
            item["sources"].append({"source": source, "value": val})


def _merge_stack_with_rules(
    stack: dict, modifiers: dict, rules: dict, source: str
) -> None:
    """Merge modifiers using simple stacking rules."""
    if not isinstance(modifiers, dict):
        return

    for category, values in modifiers.items():
        if not isinstance(values, dict):
            continue
        cat_entry = stack.setdefault(category, {})
        rule_cat = rules.get(category, {}) if isinstance(rules, dict) else {}
        for key, val in values.items():
            rule = (
                rule_cat.get(key)
                if isinstance(rule_cat, dict)
                else rule_cat
            )
            item = cat_entry.setdefault(key, {"total": 0, "sources": []})
            if rule == "max":
                item["total"] = max(item["total"], val)
            else:  # additive or unknown
                item["total"] += val
            item["sources"].append({"source": source, "value": val})


def compute_modifier_stack(db: Session, kingdom_id: int) -> dict:
    """Compute the full modifier stack with breakdown for the given kingdom."""

    stack: dict = {
        "resource_bonus": {},
        "troop_bonus": {},
        "combat_bonus": {},
        "defense_bonus": {},
        "economic_bonus": {},
        "production_bonus": {},
    }

    def load_modifier_row(sql: str, params: dict, source_label: str):
        try:
            rows = db.execute(text(sql), params).fetchall()
            for (mod,) in rows:
                if isinstance(mod, str):
                    try:
                        mod = json.loads(mod)
                    except Exception:
                        mod = {}
                _merge_stack(stack, mod or {}, source_label)
        except Exception as e:
            logging.warning(f"Failed to load modifiers from {source_label}: {e}")

    # --- Region Bonuses ---
    region_row = db.execute(
        text("SELECT region FROM kingdoms WHERE kingdom_id = :kid"),
        {"kid": kingdom_id},
    ).fetchone()
    if region_row:
        region_code = region_row[0]
        rows = db.execute(
            text(
                "SELECT bonus_type, bonus_value FROM region_bonuses WHERE region_code = :code"
            ),
            {"code": region_code},
        ).fetchall()
        for btype, val in rows:
            _merge_stack(stack, {btype: {"value": val}}, "Region Bonus")

    # --- Completed Techs ---
    load_modifier_row(
        """
        SELECT tc.modifiers FROM kingdom_research_tracking krt
        JOIN tech_catalogue tc ON tc.tech_code = krt.tech_code
        WHERE krt.kingdom_id = :kid AND krt.status = 'completed'
        """,
        {"kid": kingdom_id},
        "Tech",
    )

    # --- Active Temple Buildings ---
    load_modifier_row(
        """
        SELECT bc.modifiers FROM village_buildings vb
        JOIN kingdom_villages kv ON kv.village_id = vb.village_id
        JOIN building_catalogue bc ON bc.building_id = vb.building_id
        WHERE kv.kingdom_id = :kid
        AND bc.production_type = 'temple'
        AND vb.construction_status = 'complete'
        """,
        {"kid": kingdom_id},
        "Temples",
    )

    # --- Kingdom Projects ---
    load_modifier_row(
        """
        SELECT pc.modifiers FROM projects_player pp
        JOIN project_player_catalogue pc ON pc.project_code = pp.project_code
        WHERE pp.kingdom_id = :kid
        """,
        {"kid": kingdom_id},
        "Kingdom Project",
    )

    # --- Alliance Projects ---
    load_modifier_row(
        """
        SELECT pa.active_bonus FROM projects_alliance pa
        WHERE pa.alliance_id IN (
            SELECT alliance_id FROM alliance_members
            WHERE user_id = (SELECT user_id FROM kingdoms WHERE kingdom_id = :kid)
        ) AND pa.is_active = TRUE AND pa.build_state = 'completed'
        """,
        {"kid": kingdom_id},
        "Alliance Project",
    )

    # --- Active Treaties ---
    treaty_rows = db.execute(
        text(
            """
            SELECT tm.effect_type, tm.target, tm.magnitude
              FROM kingdom_treaties kt
              JOIN treaty_modifiers tm ON tm.treaty_id = kt.treaty_id
             WHERE (kt.kingdom_id = :kid OR kt.partner_kingdom_id = :kid)
               AND kt.status = 'active'
            """
        ),
        {"kid": kingdom_id},
    ).fetchall()
    treaty_mods: dict = {}
    for eff, tgt, mag in treaty_rows:
        if mag is None:
            continue
        bucket = treaty_mods.setdefault(eff, {})
        bucket[tgt] = bucket.get(tgt, 0) + float(mag)
    if treaty_mods:
        _merge_stack(stack, treaty_mods, "Treaty")

    # --- Spy Effects ---
    spy_row = db.execute(
        text("SELECT modifiers FROM kingdom_spies WHERE kingdom_id = :kid"),
        {"kid": kingdom_id},
    ).fetchone()
    if spy_row and spy_row[0]:
        _merge_stack(stack, spy_row[0], "Spies")

    # --- Village Modifiers ---
    try:
        v_rows = db.execute(
            text(
                """
                SELECT vm.resource_bonus,
                       vm.troop_bonus,
                       vm.construction_speed_bonus,
                       vm.defense_bonus,
                       vm.trade_bonus,
                       vm.source,
                       vm.stacking_rules
                  FROM village_modifiers vm
                  JOIN kingdom_villages kv ON kv.village_id = vm.village_id
                 WHERE kv.kingdom_id = :kid
                   AND (vm.expires_at IS NULL OR vm.expires_at > now())
                """
            ),
            {"kid": kingdom_id},
        ).fetchall()
        for rb, tb, csb, dbonus, tradeb, src, rules in v_rows:
            mod: dict = {}
            if rb:
                if isinstance(rb, str):
                    try:
                        rb = json.loads(rb)
                    except Exception:
                        rb = {}
                mod["resource_bonus"] = rb
            if tb:
                if isinstance(tb, str):
                    try:
                        tb = json.loads(tb)
                    except Exception:
                        tb = {}
                mod["troop_bonus"] = tb
            if csb:
                mod.setdefault("production_bonus", {})[
                    "construction_speed_bonus"
                ] = float(csb)
            if dbonus:
                mod.setdefault("defense_bonus", {})["village"] = float(dbonus)
            if tradeb:
                mod.setdefault("economic_bonus", {})["trade_bonus"] = float(tradeb)
            r_rules = rules or {}
            if isinstance(r_rules, str):
                try:
                    r_rules = json.loads(r_rules)
                except Exception:
                    r_rules = {}
            _merge_stack_with_rules(
                stack, mod, r_rules, src or "Village Modifier"
            )
    except Exception as e:
        logging.warning(f"Failed to load village modifiers: {e}")

    # --- Prestige Score (activity metric) ---
    # Prestige no longer grants combat bonuses. It is fetched only for display
    # purposes elsewhere in the codebase.

    # --- Global Modifiers (Events, VIP, etc.) ---
    global_mods = db.execute(
        text(
            "SELECT json_modifiers FROM global_modifier_settings WHERE is_active = true"
        )
    ).fetchall()
    for (mod,) in global_mods:
        _merge_stack(stack, mod or {}, "Global")

    return stack


def summarize_modifiers(mod_stack: dict) -> dict:
    """Flatten and summarize a modifier stack to total values only (no source trace)."""
    return {
        category: {key: data["total"] for key, data in values.items()}
        for category, values in mod_stack.items()
    }
