
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
✅ Tactical war pre-plan storage documented in [docs/war_preplans.md](docs/war_preplans.md)
✅ Alliance war participant list documented in [docs/alliance_war_participants.md](docs/alliance_war_participants.md)
✅ Alliance war master record documented in [docs/alliance_wars.md](docs/alliance_wars.md)
✅ Kingdom resources usage documented in [docs/kingdom_resources.md](docs/kingdom_resources.md)
✅ Kingdom treaties documented in [docs/kingdom_treaties.md](docs/kingdom_treaties.md)
✅ Kingdom projects catalogue documented in [docs/project_player_catalogue.md](docs/project_player_catalogue.md)
✅ Player projects table documented in [docs/projects_player.md](docs/projects_player.md)
✅ Alliance project catalogue documented in [docs/project_alliance_catalogue.md](docs/project_alliance_catalogue.md)
✅ Alliance projects runtime table documented in [docs/projects_alliance.md](docs/projects_alliance.md)
✅ Alliance quest contributions documented in [docs/quest_alliance_contributions.md](docs/quest_alliance_contributions.md)
✅ Alliance member roster uses Supabase RPC `get_alliance_members_detailed`


✅ VIP status system documented in [docs/vip_status.md](docs/vip_status.md)

✅ Kingdom troops table documented in [docs/kingdom_troops.md](docs/kingdom_troops.md)
✅ Training queue documented in [docs/training_queue.md](docs/training_queue.md)
✅ Unit stats table documented in [docs/unit_stats.md](docs/unit_stats.md)
✅ Village buildings table documented in [docs/village_buildings.md](docs/village_buildings.md)
✅ Village modifiers table documented in [docs/village_modifiers.md](docs/village_modifiers.md)
✅ Kingdoms master table documented in [docs/kingdoms.md](docs/kingdoms.md)
✅ Terrain map integration documented in [docs/terrain_map.md](docs/terrain_map.md)
✅ Final schema summary in [FINAL_SCHEMA_DOCUMENTATION.md](FINAL_SCHEMA_DOCUMENTATION.md)
✅ Noble houses documented in [docs/noble_houses.md](docs/noble_houses.md)



---

## ⚙️ Tech Stack

- HTML5 + CSS3 + Javascript (ES Modules)
- FastAPI backend (expected)
- Supabase for auth + data
- SPA-ready → Netlify optimized
- No framework (Vanilla + Modules) → lean, fast


## Development Setup

Install Python dependencies with:
```bash
pip install -r dev_requirements.txt
```

### Running the Local API

The frontend expects the FastAPI backend to be available at
`http://localhost:8000`. After installing the dependencies make sure to start the
API server in a separate terminal:

```bash
pip install -r requirements.txt
python main.py
```

When the backend is not running the static server used by `npm run serve` will
return `index.html` for requests under `/api`, leading to browser console errors
like `Invalid JSON from /api/resources`.
If the API is up you can verify everything works by visiting
`http://localhost:8000/api/progression/summary` in your browser. A JSON object
should be returned.

---

## Database Setup

The `full_schema.sql` file contains the complete table definitions used by the
game. To initialize a local database run:

```bash
psql -f full_schema.sql
```

### Supabase Configuration

Environment variables for the Supabase connection are loaded from the `.ENV` file at the project root. Copy `.env.example` to `.ENV` and update it with your credentials. Frontend pages read these values via `env.js`, which must be generated from `env.example.js`.

The key variables are:

```
SUPABASE_URL
SUPABASE_ANON_KEY
SUPABASE_SERVICE_ROLE_KEY
VITE_SUPABASE_URL
VITE_SUPABASE_ANON_KEY
MASTER_ROLLBACK_PASSWORD
```

Update these values with your project credentials to enable API access. Then copy
`env.example.js` to `env.js` so the frontend can access the public values at
runtime.

When calling Supabase REST endpoints directly you must include the project's
`apikey` and a valid `Authorization` bearer token in the request headers. The
included JavaScript modules rely on the Supabase client which sets these
automatically.

This will create all tables referenced by the frontend.

After loading the base schema, apply the SQL files in the `migrations/` folder
to keep your database up to date. These scripts also seed initial data.
For example, run the regions migration to populate the `region_catalogue`
table used on **play.html**:

```bash
psql -f migrations/2025_06_08_add_regions.sql
```

Without this migration the `/api/kingdom/regions` request will fall back to
sample regions bundled with the backend, so the dropdown will work but won't
reflect any custom data you expected.

---

## Testing

Use the provided helper to run the Python test suite in restricted environments:

```bash
python -m venv venv && source venv/bin/activate
pip install -r dev_requirements.txt
pytest
```

You can run these commands directly or simply execute:

```bash
./scripts/run_tests.sh
```

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
Current deployed version → `v6.12.2025.13.16`
Pre-Alpha build — **feature-complete** FrontEnd.

---

# 🚀 GLORY TO THE KINGDOM!
