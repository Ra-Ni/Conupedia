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


@router.get('/signup')
async def signup(request: Request, sessionID: Optional[str] = Cookie(None)):
    if sessionID:
        return RedirectResponse(url='/dashboard')

    return TEMPLATES.TemplateResponse('signup.html', context={'request': request})


@router.post('/signup')
async def signup(request: Request,
                 fName: str = Form(...),
                 lName: str = Form(...),
                 email: str = Form(...),
                 password: str = Form(...),
                 sessionID: Optional[str] = Cookie(None)
                 ):
    query = users.exists_email(email)

    async with httpx.AsyncClient() as client:
        response = await client.get(SPARQL, params=query)
        response = base.to_frame(response)
        exists = bool(response.iat[0, 0])

        if exists:
            email_feedback = 'Email already exists'
            return TEMPLATES.TemplateResponse('signup.html',
                                              context={'request': request, 'email_feedback': email_feedback})

        query = users.new(fName, lName, email, password)
        await client.get(SPARQL, params=query)

    return RedirectResponse(url='/login', status_code=status.HTTP_302_FOUND)
