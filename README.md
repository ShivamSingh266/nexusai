# NexusAI — SIH26134

AI skill-gap platform for the Government of Maharashtra. Monorepo: backend,
frontend, ML training, datasets, and docs all live here so integration
happens through PRs into `develop`, not across six separate repos.

## Repo map

| Folder | Owns |
|---|---|
| `backend/` | FastAPI service — all API routes and business logic |
| `frontend/` | UI — one folder per Figma screen in `src/screens/` |
| `ml/` | Model training scripts (forecasting, embeddings) — NOT imported by the backend at runtime; exports models/weights the backend loads |
| `datasets/` | Raw/processed data + the seed script's source data |
| `docs/` | Per-member blueprints, API reference, data contracts between members |
| `infra/` | `docker-compose.yml` to run everything together locally |

Each file under `backend/app/core/` and `backend/app/api/` has an
`# OWNER:` comment at the top — that's your assignment, work in that file,
don't create a personal folder.

## Run everything locally

```bash
cd infra
cp .env.example .env
docker compose up --build
```
- Backend: http://localhost:8000/docs
- Frontend: http://localhost:5173
- Postgres: localhost:5432 (user/pass: nexusai/nexusai)

## Run backend only (faster iteration)

```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
export DATABASE_URL="sqlite:///./dev.db"   # or point at the docker postgres
python -m app.seed
uvicorn app.main:app --reload
```

## Branch workflow

- `main` — stable/deployable
- `develop` — integration branch, everyone PRs into here
- `feature/<name>-<scope>` — your working branch, branched off `develop`

```bash
git checkout develop
git pull
git checkout -b feature/<yourname>-<scope>
# ... work, commit ...
git push -u origin feature/<yourname>-<scope>
# open PR into develop on GitHub
```

## Status

See `docs/blueprints/` for the original per-member specs and
`docs/member5_backend_notes.md` for what's built and tested so far
(gap/matching/roadmap/shortlist/what-if engine — Member 5's scope).
