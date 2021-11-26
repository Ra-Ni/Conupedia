from typing import Optional
import httpx
import shortuuid
from fastapi import APIRouter, Request, Cookie, Form
from starlette import status
from starlette.responses import RedirectResponse
from ..internals.globals import TEMPLATES
from ..dependencies import core
from ..internals import namespaces


router = APIRouter()


@router.get('/signup')
async def signup(request: Request, token: Optional[str] = Cookie(None)):
    if token:
        return RedirectResponse(url='/dashboard')

    return TEMPLATES.TemplateResponse('signup.html', context={'request': request})


@router.post('/signup')
async def signup(request: Request,
                 fName: str = Form(...),
                 lName: str = Form(...),
                 email: str = Form(...),
                 password: str = Form(...),
                 token: Optional[str] = Cookie(None)
                 ):
    if token:
        return RedirectResponse(url='/dashboard', status_code=302)

    async with httpx.AsyncClient() as client:
        query = """
        ask from %s { ?s foaf:mbox "%s" } 
        """ % (namespaces.ssu, email)
        response = await core.send(client, query, 'bool')
        if response:
            context = {'request': request, 'email_feedback': 'Email already exists'}
            return TEMPLATES.TemplateResponse('signup.html', context=context)

        user_id = shortuuid.uuid()
        query = """
            insert in graph %s {
               ssu:%s a foaf:Person ;
                   rdfs:label "%s" ; 
                   foaf:firstName "%s" ;
                   foaf:lastName "%s" ;
                   foaf:mbox "%s" ;
                   schema:accessCode "%s" ;
                   sso:status "active" .
            }
            """ % (namespaces.ssu, user_id, user_id, fName, lName, email, base.hash_password(password))
        await core.send(client, query)

    return RedirectResponse(url='/login', status_code=status.HTTP_302_FOUND)
