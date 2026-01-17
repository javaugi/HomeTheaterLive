# backend/app/api/routes/recommendations.py
from typing import Any
from fastapi import APIRouter

from app.api.deps import (
    CurrentUser,
    SessionDep,
)
from app.models import (
    Item,
)


router = APIRouter(prefix="/recommendations", tags=["recommendations"])

@router.get("/", response_model=list[Item])
def get_recommendations(
    current_user: CurrentUser, 
    session: SessionDep,
    limit: int = 10
) -> Any:
    # Logic to fetch recommendations
    print(f"getRecommendations get user me id, {current_user.id}, email to {current_user.email}")
    return []