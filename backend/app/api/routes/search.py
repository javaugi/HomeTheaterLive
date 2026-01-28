print(">>> importing backend/app/api/routes/search.py")
from typing import Any
from fastapi import APIRouter

from app.api.deps import (
    CurrentUser,
    SessionDep,
)
from app.models import (
    Item,
)

router = APIRouter(prefix="/search", tags=["search"])
print(">>> importing backend/app/api/routes/search.py done")

@router.get("/", response_model=list[Item])
def get_search(
    current_user: CurrentUser, 
    session: SessionDep,
    limit: int = 10
) -> Any:
    # Logic to fetch recommendations
    print(f"get_search get user me id, {current_user.id}, email to {current_user.email}")
    return []