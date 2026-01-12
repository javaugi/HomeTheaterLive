
from fastapi import Depends, HTTPException
from enum import Enum

class Role(str, Enum):
    user = "user"
    admin = "admin"

def require_role(required: Role):
    def checker(current_user=Depends(lambda: {"role": "user"})):
        if current_user["role"] != required:
            raise HTTPException(status_code=403, detail="Insufficient role")
        return current_user
    return checker
