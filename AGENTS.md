# AGENTS Instructions for Thronestead

This repository contains the pre-alpha frontend and accompanying FastAPI backend of **Thronestead**. Use the following steps and conventions when working in this code base.

## Local Setup

1. **Database**
   - Ensure PostgreSQL is available. The backend defaults to `postgresql://postgres:postgres@localhost/postgres` unless `DATABASE_URL` is set.
   - Initialize the schema:
     ```bash
     psql -f full_schema.sql
     ```

2. **Environment Variables**
   - Edit `.env` with your Supabase credentials (`SUPABASE_URL`, `SUPABASE_ANON_KEY`).
   - Optionally set `API_BASE_URL` if your backend runs on a different host.
   - If you have a service role key, set `SUPABASE_SERVICE_ROLE_KEY` as well.
  - Environment variables prefixed with `VITE_` are automatically exposed to the frontend via Vite.

3. **Backend**
   - Install Python dependencies and run the API:
     ```bash
     pip install -r backend/requirements.txt
     python main.py
     ```
   - The FastAPI server will listen on `http://localhost:8000`.

4. **Frontend**
   - Install Node dependencies and start the static server:
     ```bash
     npm install
     npm run serve
     ```
   - The site will be served at `http://localhost:3000`.

## Testing

- Run the Python test suite with `pytest` from the repository root.
- The frontend currently has no automated tests (`npm test` prints "No tests defined").

## Style Guidelines

- **Python** code follows standard 4‑space indentation.
- **JavaScript** uses 2‑space indentation and ES modules.
- Avoid introducing frameworks; the frontend is intentionally framework‑free.
- New backend endpoints should include corresponding tests in `tests/`.

## Deployment

- `render.yaml` deploys only the FastAPI backend on Render.
- The frontend is served separately on Netlify using `netlify.toml`.

---

Keep this file up to date if setup or workflow steps change.
