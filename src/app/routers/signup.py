import os
import uuid
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
        return RedirectResponse(url='/dashboard', status_code=status.HTTP_302_FOUND)

    fName = fName.title()
    lName = lName.title()
    async with httpx.AsyncClient() as client:
        query = """
        ask from %s { ?s foaf:mbox "%s" } 
        """ % (namespaces.ssu, email)
        response = await core.send(client, query, 'bool')
        if response:
            context = {'request': request, 'email_feedback': 'Email already exists'}
            return TEMPLATES.TemplateResponse('signup.html', context=context)

        user_id = shortuuid.uuid()
        verification_id = uuid.uuid4().hex
        query = """
            insert in graph %s {
               ssu:%s a foaf:Person ;
                   rdfs:label "%s" ; 
                   foaf:firstName "%s" ;
                   foaf:lastName "%s" ;
                   foaf:mbox "%s" ;
                   schema:accessCode "%s" ;
                   sso:hasVerification "%s" ;
                   sso:status "inactive" .
            }
            """ % (namespaces.ssu, user_id, user_id, fName, lName, email, core.hash_password(password), verification_id)
        await core.send(client, query)
        _send_mail(verification_id, email, fName, lName)

    context = {'request': request, 'general_feedback': 'Successfully created account. '
                                                       'Please check your email for activation.'}
    return TEMPLATES.TemplateResponse('signup.html', context=context)


def _send_mail(verification: str, email: str, firstname: str, lastname: str):
    message = """<b>Welcome to Conupedia, %s %s!</b><br>\
    <p>To complete your registration, please click on this \
    <a href="http://securesea.ca/verify?id=%s">link</a></p>""" % (firstname, lastname, verification)

    command = """echo "%s" | mail -s "Conupedia Registration" \
    -a "Content-Type: text/html" \
    -a "From: no-reply <mySecureSea@gmail.com>" %s""" % (message, email)

    os.system(command)
