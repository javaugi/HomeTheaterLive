1️⃣ Final Architecture
┌─────────────────────────┐
│  BeeWare Mobile App     │
│  (Python + Toga)        │
│                         │
│  - Login                │
│  - Secure token store   │
│  - API client           │
└───────────┬─────────────┘
            │ HTTPS + JWT
┌───────────▼─────────────┐
│ FastAPI Backend         │
│ (full-stack template)   │
│                         │
│ - OAuth2/JWT            │
│ - PostgreSQL            │
│ - Alembic               │
└───────────┬─────────────┘
            │
┌───────────▼─────────────┐
│ Cloud Infra             │
│ Fly.io / GCP / AWS      │
└─────────────────────────┘
