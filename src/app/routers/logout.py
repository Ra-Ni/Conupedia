import re
from typing import Optional
import httpx
import pandas as pd
from fastapi import APIRouter, Request, Response, Cookie, Form
from starlette import status
from starlette.responses import RedirectResponse
from ..internals.globals import TEMPLATES, SPARQL
from ..virtuoso import users, base, auth, recommendations
from ..internals import namespaces


router = APIRouter()


@router.get('/logout')
async def logout(request: Request, sessionID: Optional[str] = Cookie(None)):
    if not sessionID:
        return RedirectResponse(url='/login')

    query = auth.delete(sessionID)
    async with httpx.AsyncClient() as client:
        await client.get(SPARQL, params=query)

    response = RedirectResponse(url='/login')
    response.delete_cookie(key='sessionID')
    return response
