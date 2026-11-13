# Agri-OS 2026 Android PWA — GitHub Pages (free-tier starter)

This is a **read-only, static PWA**. It is not a verified radar nowcast or a full 21-source operational system. It uses the prior Python ECMWF/ThaiWater prototype. The website does **not** expose API keys or public refresh/write endpoints.

## Install from Android (no PC required)
1. Create a GitHub account and a **public** repository, e.g. `agri-os-2026` (public GitHub Pages is supported on GitHub Free; check current terms/usage limits).
2. Extract the ZIP using Android Files. Upload the **contents** of this folder to the repository root, including `.github/workflows/publish.yml`. GitHub's mobile upload interface may hide dot-folders; use the GitHub website in Chrome with **Desktop site** or upload using a Git-capable Android app. Confirm `.github/workflows/publish.yml` appears in the repository.
3. Repository **Settings → Pages → Build and deployment → Source: GitHub Actions**.
4. Open **Actions → Build and publish Agri-OS PWA → Run workflow**. Wait for a green successful run; inspect the job logs for API errors.
5. Open `https://YOUR_USERNAME.github.io/agri-os-2026/` (replace username/repository name). In Chrome Android: **⋮ → Add to Home screen → Install** (wording may vary).
6. Every 3 hours the workflow *attempts* an update; GitHub scheduled workflows may be delayed or disabled after inactivity. The UI shows stale-report warnings after 6 hours. The **โหลดรายงานอีกครั้ง** button only re-fetches the already published report; it does not invoke live model updates.

## Run locally
`python build.py --offline` generates a safe missing-data report without API calls. `python build.py` attempts live ECMWF and ThaiWater calls. For preview, run `python -m http.server 8000 -d docs` then open `http://localhost:8000`.

## Verification and limitations
- GitHub Actions execution is free within applicable plan/usage limits; a public repository means all published report files are publicly visible. Do not add private locations, secrets or credentials.
- The original engine queries two Chumphon reference points. It does **not** calculate forecasts for all districts/provinces, or confirm ThaiWater endpoint schemas.
- `received` only means an HTTP JSON response was parsed; it does not independently verify station quality, freshness, or radar imagery. Inspect logs and source timestamps.
- Rainfall threshold >=90 mm is a **user-defined flag** for a table period, not an official warning threshold. Smaller totals can still be dangerous.
- Hourly ECMWF forecasts are **not** radar-based 0–6 hour nowcasts.
- PWA shell can be opened offline, but weather data requires a network connection. Failed loads do not silently reuse stale reports.
- A free GitHub Pages site cannot run Python on demand. The scheduled Actions job runs Python and publishes JSON.

## Next engineering tasks
Validate endpoint schema and timestamp; add per-source retry/backoff and freshness gates; ingest TMD radar and satellite products with permission and proper attribution; 77-province gridded dataset; time-matched ground-truth archive; verified MAE/RMSE and calibrated ensemble; safe soil-water-balance input collection; user authentication if private farms are introduced.
