This is a very good question, and you’ve actually hit a real-world gotcha with the template flow.
Right now, nothing is “wrong” with BeeWare or Briefcase — your backend is simply not ready to authenticate test / test yet.

Let’s walk through exactly how to make local login succeed, step by step, with zero guesswork.

🔴 Why test / test Fails Right Now
Out of the box, beeware-fastapi-mobile-enterprise does NOT create users automatically.
So when you do:
    username: test
    password: test

FastAPI correctly says:
❌ 401 Unauthorized

Because:
    No user exists
    Password not hashed
    No DB initialized

✅ Correct Local Testing Setup (Minimal & Reliable)

We’ll do this in 4 steps:

1️⃣ Start backend
2️⃣ Create a test user
3️⃣ Verify login via curl
4️⃣ Login from BeeWare app

✅ Correct Local Testing Setup (Minimal & Reliable)

We’ll do this in 4 steps:

1️⃣ Start backend
2️⃣ Create a test user
3️⃣ Verify login via curl
4️⃣ Login from BeeWare app

1️⃣ Start the Backend (Local)
From the project root:
cd backend
    uvicorn app.main:app --reload
You should see:
    Uvicorn running on http://127.0.0.1:8000

2️⃣ Create a Test User (REQUIRED)
Option A — One-Time Dev Seed (Recommended)
Create this file:

backend/app/dev_seed.py

python -c "from app.dev_seed import create_test_user; create_test_user()"
✔ This creates test / test properly