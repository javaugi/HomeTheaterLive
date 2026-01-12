
# Placeholder for JWT revocation table logic
# In production, back this with PostgreSQL / Redis

revoked_tokens = set()

def revoke(jti: str):
    revoked_tokens.add(jti)

def is_revoked(jti: str) -> bool:
    return jti in revoked_tokens
