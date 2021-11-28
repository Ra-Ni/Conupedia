from typing import Optional
import httpx
from fastapi import APIRouter, Request, Response, Cookie, Form
from starlette import status
from starlette.responses import RedirectResponse
from ..dependencies import auth, core
from ..internals.globals import TEMPLATES
from ..internals import namespaces

router = APIRouter()


@router.get('/login')
async def login(request: Request, token: Optional[str] = Cookie(None)):
    try:
        async with httpx.AsyncClient() as client:
            await auth.verify(client, token)
            return RedirectResponse(url='/dashboard')
    except auth.InvalidCredentials:
        return TEMPLATES.TemplateResponse('login.html', context={'request': request})


@router.post('/login')
async def login(request: Request, response: Response, email: str = Form(...), password: str = Form(...)):
    async with httpx.AsyncClient() as client:
        context = {'request': request}
        query = """
        select ?id ?firstName ?lastName ?password ?status
        where { 
            graph %s {
                ?id foaf:firstName ?firstName ;
                    foaf:lastName ?lastName ;
                    foaf:mbox "%s" ;
                    schema:accessCode ?password ;
                    sso:status ?status ;
            }
        } 
        """ % (namespaces.ssu, email)
        response = await core.send(client, query, format='dict')

        if not response:
            context['email_feedback'] = " The email you entered isn't connected to an account. "
            return TEMPLATES.TemplateResponse('login.html', context=context)

        if response['status'] == 'inactive':
            context['general_feedback'] = " The account you entered has not been activated yet. "
            return TEMPLATES.TemplateResponse('login.html', context=context)

        if response['password'] != core.hash_password(password):
            context['password_feedback'] = " The password you entered is incorrect. "
            return TEMPLATES.TemplateResponse('login.html', context=context)

        token = await auth.create(client, response['id'])

    response = RedirectResponse(url='/login', status_code=status.HTTP_302_FOUND)
    response.set_cookie('token', token)
    return response
