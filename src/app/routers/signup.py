import os
import uuid
from typing import Optional
import httpx
import shortuuid
from fastapi import APIRouter, Request, Cookie, Form
from starlette import status
from starlette.responses import RedirectResponse

from . import user
from ..dependencies.core import hash_password
from ..internals.globals import TEMPLATES, SSU
from ..dependencies import core, auth

router = APIRouter()


@router.get('/signup')
async def signup(request: Request, token: Optional[str] = Cookie(None)):
    return TEMPLATES.TemplateResponse('signup.html', context={'request': request})


@router.post('/signup')
async def signup(request: Request,
                 first_name: str = Form(...),
                 last_name: str = Form(...),
                 email: str = Form(...),
                 password: str = Form(...),
                 token: Optional[str] = Cookie(None)
                 ):

    first_name = first_name.title()
    last_name = last_name.title()
    password = hash_password(password)

    context = {'request': request}
    response = await user.exists(email)
    if response.status_code != status.HTTP_200_OK:
        context['email_feedback'] = 'Email already exists'
        return TEMPLATES.TemplateResponse('signup.html', context=context)

    uid = await user.post(email, password, first_name, last_name)
    profile = {
        'id': uid,
        'first_name': first_name,
        'last_name': last_name,
        'email': email,
        'password': password,
        'state': 'inactive'
    }
    response = await auth.post(profile)
    verification_id = response.background
    if response.status_code != status.HTTP_200_OK:
        context['general_feedback'] = 'Oops. Something went wrong.'
    # _send_mail(verification_id, email, fName, lName)
    else:
        context['general_feedback'] ='Successfully created account. Please check your email for activation.'
        return TEMPLATES.TemplateResponse('signup.html', context=context)


def _send_mail(verification: str, email: str, firstname: str, lastname: str):
    message = """<b>Welcome to Conupedia, %s %s!</b><br>\
    <p>To complete your registration, please click on this \
    <a href="http://securesea.ca/verify?id=%s">link</a></p>""" % (firstname, lastname, verification)

    command = """echo "%s" | mail -s "Conupedia Registration" \
    -a "Content-Type: text/html" \
    -a "From: no-reply <mySecureSea@gmail.com>" %s""" % (message, email)

    os.system(command)
