print(">>> importing backend/app/api/routes/devices.py")
from typing import Any
from fastapi import APIRouter

from app.api.deps import (
    CurrentUser,
    SessionDep,
)
from app.models import (
    Item,
)


router = APIRouter(prefix="/devices", tags=["devices"])
print(">>> importing backend/app/api/routes/devices.py done")

@router.get("/", response_model=list[Item])
def get_devices(
    current_user: CurrentUser, 
    session: SessionDep,
    limit: int = 10
) -> Any:
    # Logic to fetch recommendations
    print(f"get_devices get user me id, {current_user.id}, email to {current_user.email}")
    return []