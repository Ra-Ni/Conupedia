from typing import Optional
import httpx
from fastapi import APIRouter, Request, Cookie, Form
from ..internals.globals import TEMPLATES, SSU, SST
from ..dependencies import auth, core

router = APIRouter()


@router.get('/profile')
async def profile(request: Request, token: Optional[str] = Cookie(None), profileID: Optional[str] = Cookie(None)):
    async with httpx.AsyncClient() as client:
        user = await auth.get_user(client, token)
        context = {'request': request, 'user_info': user}

    return TEMPLATES.TemplateResponse('setting.html', context=context)


@router.post('/profile')
async def profile(request: Request,
                  current_password: str = Form(...),
                  new_password: str = Form(...),
                  confirm_new_password: str = Form(...),
                  token: Optional[str] = Cookie(None)):
    async with httpx.AsyncClient() as client:
        user = await auth.get_user(client, token)
        context = {'request': request, 'user_info': user, 'password_feedback': None}

        if new_password != confirm_new_password:
            context['password_error'] = "Passwords do not match."
            return TEMPLATES.TemplateResponse('setting.html', context=context)

        if user['password'] != core.hash_password(current_password):
            context['password_error'] = "Incorrect input for current password."
            return TEMPLATES.TemplateResponse('setting.html', context=context)

        query = """
            modify %s 
            delete { ?s schema:accessCode ?o }
            insert { ?s schema:accessCode "%s" }
            where {
                graph %s {
                    [] a sso:Token ;
                        rdfs:seeAlso ?s ;
                        rdf:value "%s" .
                }
                graph %s {
                    ?s schema:accessCode ?o .
                }
            }
            """ % (SSU, core.hash_password(new_password), SST, token, SSU)
        await core.send(client, query)

        context['password_feedback'] = "Password updated successfully."
        return TEMPLATES.TemplateResponse('setting.html', context=context)
