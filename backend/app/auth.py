from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader
from app.config import API_KEY

_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def require_api_key(api_key: str = Security(_api_key_header)) -> None:
    if not API_KEY:
        return  # auth not configured — open access (dev / trusted LAN)
    if api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
