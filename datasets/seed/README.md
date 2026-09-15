The executable seed script lives at `backend/app/seed.py` (it needs the
SQLAlchemy models, so it can't live outside the backend package cleanly).

This folder holds the *raw source data* that seed.py is built from once
real datasets replace the hardcoded demo values — e.g. a `skills.csv` from
Member 4, `courses.csv` from whoever owns course scraping, etc.
