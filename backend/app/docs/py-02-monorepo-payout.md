2️⃣ Monorepo Layout (Recommended)
myhometheater/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── models/
│   │   └── main.py
│   ├── alembic/
│   ├── Dockerfile
│   └── pyproject.toml
│
├── mobile/
│   ├── pyproject.toml
│   ├── src/myhometheater/
│   │   ├── app.py
│   │   ├── api.py
│   │   ├── auth.py
│   │   ├── storage.py
│   │   └── views/
│   │       ├── login.py
│   │       └── home.py
│
└── .github/workflows/
    ├── backend.yml
    ├── ios.yml
    └── android.yml
