# -*- coding: utf-8 -*-
# test_startup.py
print("Testing imports...")

try:
    from app.api.endpoints import router
    print("✓ Successfully imported videos router")
except Exception as e:
    print(f"✗ Failed to import videos router: {e}")
    import traceback
    traceback.print_exc()

try:
    from app.db.session import engine
    from app.db.base import Base
    print("✓ Successfully imported database modules")
except Exception as e:
    print(f"✗ Failed to import database modules: {e}")
    import traceback
    traceback.print_exc()
