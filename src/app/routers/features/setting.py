from typing import Optional
import httpx
from fastapi import APIRouter, Request, Cookie, Form
from app.internals.globals import TEMPLATES, SSU
from app.dependencies import core

router = APIRouter()


@router.get('/setting')
async def profile(request: Request, token: Optional[str] = Cookie(None), profileID: Optional[str] = Cookie(None)):
    user_profile = request.state.user
    async with httpx.AsyncClient() as client:
        context = {'request': request, 'user_profile': user_profile}

    return TEMPLATES.TemplateResponse('setting.html', context=context)


@router.post('/setting')
async def profile(request: Request,
                  current_password: str = Form(...),
                  new_password: str = Form(...),
                  confirm_new_password: str = Form(...),
                  token: Optional[str] = Cookie(None)):
    user_profile = request.state.user
    uid = user_profile['id']
    password = user_profile['password']
    context = {'request': request, 'user_profile': user_profile, 'password_feedback': None}

    if password != core.hash_password(current_password):
        context['password_error'] = "Incorrect input for current password."
        return TEMPLATES.TemplateResponse('setting.html', context=context)

    if new_password != confirm_new_password:
        context['password_error'] = "Passwords do not match."
        return TEMPLATES.TemplateResponse('setting.html', context=context)

    new_password = core.hash_password(new_password)
    query = """
    modify %s 
    delete { ssu:%s schema:accessCode "%s" }
    insert { ssu:%s schema:accessCode "%s" }
    """ % (SSU, uid, password, uid, new_password)

    async with httpx.AsyncClient() as client:
        await core.send(client, query)
        context['password_feedback'] = "Password updated successfully."
        return TEMPLATES.TemplateResponse('setting.html', context=context)
