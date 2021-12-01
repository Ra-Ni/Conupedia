import json
from typing import Optional
import httpx
from fastapi import APIRouter, Request, Response, Cookie, Form
from starlette import status
from starlette.responses import RedirectResponse

from . import user
from ..dependencies import auth, core
from ..dependencies.core import hash_password
from ..internals.globals import TEMPLATES, SSU

router = APIRouter()


@router.get('/login')
async def login(request: Request, token: Optional[str] = Cookie(None)):
    return TEMPLATES.TemplateResponse('login.html', context={'request': request})


@router.post('/login')
async def login(request: Request, response: Response, email: str = Form(...), password: str = Form(...)):
    context = {'request': request}
    password = hash_password(password)
    response = await user.get(email)
    if response.status_code != status.HTTP_200_OK:
        context['email_feedback'] = "The email you entered isn't connected to an account."
        return TEMPLATES.TemplateResponse('login.html', context=context)

    response = json.loads(response.body)

    if response['status'] == 'inactive':
        context['general_feedback'] = " The account you entered has not been activated yet. "
        return TEMPLATES.TemplateResponse('login.html', context=context)

    if response['password'] != password:
        context['password_feedback'] = " The password you entered is incorrect. "
        return TEMPLATES.TemplateResponse('login.html', context=context)

    token = await auth.post(response)

    response = RedirectResponse(url='/', status_code=status.HTTP_302_FOUND)
    response.set_cookie('token', token.background)
    return response
