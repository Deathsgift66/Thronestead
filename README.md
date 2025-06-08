
Auth is handled via **Supabase Client** → included in `supabaseClient.js`.

New sign-ups automatically create the associated profile and starter kingdom
records using Supabase row level security.

A unique constraint on `kingdoms.user_id` ensures each player can only
own a single kingdom.

See [docs/onboarding_setup.md](docs/onboarding_setup.md) for a breakdown of
the records created during onboarding.

---

## ✅ Features Implemented

✅ Dynamic Navbar (auth-aware)  
✅ authGuard.js protection on restricted pages
✅ Global public page policy for index/login/signup/legal
✅ Alliance System → full suite
✅ Alliance Treaties diplomacy
✅ Military → full recruitment + war system
✅ Market & Trade Center  
✅ Sovereign’s Grand Overseer (VIP 2 panel)  
✅ Dynamic World Map → zoom, pan, click  
✅ Quests + Projects System  
✅ Admin Dashboard → full logs + actions
✅ Comprehensive audit log of player and admin activity
✅ Seasonal Effects → dynamic
✅ GDPR / Legal Ready → legal.html + linked PDFs  
✅ Lighthouse / SEO optimized
✅ Progression stages documented in [docs/kingdom_progression_stages.md](docs/kingdom_progression_stages.md)
✅ Progression gating documented in [docs/page_access_gating.md](docs/page_access_gating.md)
✅ Alliance war pre-plan storage documented in [docs/alliance_war_preplans.md](docs/alliance_war_preplans.md)
✅ Alliance war participant list documented in [docs/alliance_war_participants.md](docs/alliance_war_participants.md)
✅ Alliance war master record documented in [docs/alliance_wars.md](docs/alliance_wars.md)
✅ Kingdom resources usage documented in [docs/kingdom_resources.md](docs/kingdom_resources.md)
✅ Kingdom treaties documented in [docs/kingdom_treaties.md](docs/kingdom_treaties.md)
✅ Kingdom troops table documented in [docs/kingdom_troops.md](docs/kingdom_troops.md)


---

## ⚙️ Tech Stack

- HTML5 + CSS3 + Javascript (ES Modules)
- FastAPI backend (expected)
- Supabase for auth + data
- SPA-ready → Netlify optimized
- No framework (Vanilla + Modules) → lean, fast

---

## Database Setup

The `full_schema.sql` file contains the complete table definitions used by the
game. To initialize a local database run:

```bash
psql -f full_schema.sql
```

This will create all tables referenced by the frontend.

---

## 📝 License

Proprietary — Kingmaker’s Rise Project.  
All rights reserved.

No public redistribution or derivative works without explicit permission.

---

## 👑 Author

Developed by: **Deathsgift66**  
Date: **June 2, 2025**

---

**For testers:**  
Current deployed version → `v6.2.25`  
Pre-Alpha build — **feature-complete** FrontEnd.

---

# 🚀 GLORY TO THE KINGDOM!
