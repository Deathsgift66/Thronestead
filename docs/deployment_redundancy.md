# Deployment-Level Redundancy

Thronestead uses a multi-host approach to minimize downtime. The static frontend is deployed on both **Netlify** and **Vercel**. Netlify serves as the primary host while Vercel stays in warm-standby. External uptime monitoring services such as UptimeRobot should ping each host every 60 seconds to detect failures quickly.

The FastAPI backend defined in `render.yaml` is deployed on Render. A second Render service running the same container can be provisioned under a separate domain. Set `BACKUP_API_BASE_URL` to this domain so the frontend can fall back to it when needed.

When API requests return a `5xx` error during a `POST`, the helper in `Javascript/apiHelper.js` automatically retries the request using `BACKUP_API_BASE_URL`. This keeps actions functional if the primary backend becomes unavailable.

Make sure environment variables (`VITE_API_BASE_URL` and `VITE_BACKUP_API_BASE_URL`) are configured in both Netlify and Vercel.

