from typing import Optional
import httpx
from fastapi import APIRouter, Cookie
from starlette.responses import RedirectResponse
from ..dependencies import auth


router = APIRouter()


@router.get('/logout')
async def logout(token: Optional[str] = Cookie(None)):
    async with httpx.AsyncClient() as client:
        await auth.verify(client, token)
        await auth.delete(client, token)
        response = RedirectResponse(url='/login')
        response.delete_cookie(key='token')
        return response
