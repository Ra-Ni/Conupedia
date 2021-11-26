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


@router.get('/profile')
async def profile(request: Request, sessionID: Optional[str] = Cookie(None), profileID: Optional[str] = Cookie(None)):
    if not sessionID:
        return RedirectResponse(url=router.url_path_for('login'), status_code=status.HTTP_302_FOUND)

    query = users.from_token(sessionID)
    context = {'request': request, 'user_info': None}

    async with httpx.AsyncClient() as client:
        response = await client.get(SPARQL, params=query)
        response = base.to_frame(response)
        context['user_info'] = response.to_dict('records')[0]

    return TEMPLATES.TemplateResponse('setting.html', context=context)


@router.post('/profile')
async def profile(request: Request,
                  current_password: str = Form(...),
                  new_password: str = Form(...),
                  confirm_new_password: str = Form(...),
                  sessionID: Optional[str] = Cookie(None)):
    if not sessionID:
        return RedirectResponse(url='/login', status_code=status.HTTP_302_FOUND)
    context = {'request': request, 'password_feedback': None}

    if new_password != confirm_new_password:
        context['password_error'] = "Passwords do not match."
        return TEMPLATES.TemplateResponse('setting.html', context=context)

    query = users.from_token(sessionID)
    async with httpx.AsyncClient() as client:
        response = await client.get(SPARQL, params=query)
        response = base.to_frame(response)
        credentials = context['user_info'] = response.to_dict('records')[0]

        if credentials['password'] != base.hash_password(current_password):
            context['password_error'] = "Incorrect input for current password."
            return TEMPLATES.TemplateResponse('setting.html', context=context)

        query = users.update_password(sessionID, new_password)
        response = await client.get(SPARQL, params=query)

    context['password_feedback'] = "Password updated successfully."
    return TEMPLATES.TemplateResponse('setting.html', context=context)
