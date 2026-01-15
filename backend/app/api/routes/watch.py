from typing import Any
from fastapi import APIRouter

from app.api.deps import (
    CurrentUser,
    SessionDep,
)
from app.models import (
    Item,
)


# In watch.py
router = APIRouter(prefix="/watch", tags=["watch"])

@router.get("/continue", response_model=list[Item])  # Assuming you have an Item model
def get_continue_watching(current_user: CurrentUser, session: SessionDep) -> Any:
    # Logic to fetch user's continue watching items
    print(f"watchContinue get user me id, {current_user.id}, email to {current_user.email}")
    return []