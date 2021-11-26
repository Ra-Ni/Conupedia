from typing import Optional
import httpx
from fastapi import APIRouter, Request, Response, Cookie, Form
from starlette import status
from starlette.responses import RedirectResponse
from ..internals.globals import TEMPLATES, SPARQL
from ..virtuoso import users, base, auth


router = APIRouter()


@router.get('/login')
async def login(request: Request, response: Response, sessionID: Optional[str] = Cookie(None)):
    if sessionID:
        return RedirectResponse(url='/dashboard')

    return TEMPLATES.TemplateResponse('login.html', context={'request': request})


@router.post('/login')
async def login(request: Request, response: Response, email: str = Form(...), password: str = Form(...)):
    context = {'request': request}
    query = users.from_email(email)

    async with httpx.AsyncClient() as client:
        response = await client.get(SPARQL, params=query)
        response = base.to_frame(response)

        if response.empty:
            context['email_feedback'] = " The email you entered isn't connected to an account. "
            return TEMPLATES.TemplateResponse('login.html', context=context)

        response = response.to_dict('records')[0]

        if response['password'] != base.hash_password(password):
            context['password_feedback'] = " The password you entered is incorrect. "
            return TEMPLATES.TemplateResponse('login.html', context=context)

        query, token = auth.new(response['id'])
        await client.get(SPARQL, params=query)

    response = RedirectResponse(url='/login', status_code=status.HTTP_302_FOUND)
    response.set_cookie('sessionID', token)
    return response
