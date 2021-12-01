from typing import Optional
import httpx
from fastapi import APIRouter, Cookie
from starlette.responses import RedirectResponse
from app.dependencies import auth

router = APIRouter()


@router.get('/logout')
async def logout():
    response = RedirectResponse(url='/login')
    response.delete_cookie(key='token')
    return response
