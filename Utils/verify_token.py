from fastapi import HTTPException, status, Header

# Define a simple token for development
STATIC_DEV_TOKEN = "dev-static-token-123"

def verify_token(authorization: str = Header(...)) -> str:
    """
    Dummy token verification for development.
    Expects a token in the Authorization header like: Bearer dev-static-token-123
    """
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format",
        )

    token = authorization.split(" ")[1]

    if token != STATIC_DEV_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )
    
    return token  # return user info in real implementation
