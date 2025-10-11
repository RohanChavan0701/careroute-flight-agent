from typing import Optional
from fastapi import Header, HTTPException, status

from .settings import settings


async def require_api_key(x_api_key: Optional[str] = Header(default=None)) -> None:
    """Simple API key header guard using `x-api-key`.

    - Rejects missing or mismatched keys with 401.
    - Does not log the provided key.
    """
    if not x_api_key or x_api_key != settings.api_key:
        # Avoid echoing keys; generic error
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")


