import datetime
import re
from asyncio.log import logger
from typing import Optional

import requests
import uvicorn
from fastapi import FastAPI, Form, Request, Depends, HTTPException, Response, Cookie
from fastapi.templating import Jinja2Templates
from fastapi.security import OAuth2PasswordBearer
from fastapi.staticfiles import StaticFiles
import uuid

from starlette import status
from starlette.responses import RedirectResponse

import virtuoso
from password import hash_password

app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
templates = Jinja2Templates(directory="web/")
app.mount('/web', StaticFiles(directory='web'), name='web')
URI = 'http://192.168.0.4:8890/sparql'


@app.get('/register')
def register(request: Request):
    return templates.TemplateResponse('sign-up/index.html', context={'request': request})


@app.post('/register')
def register(request: Request,
             fName: str = Form(...),
             lName: str = Form(...),
             email: str = Form(...),
             password: str = Form(...),
             cpassword: str = Form(...)
             ):
    if password != cpassword:
        feedback = 'Password does not match'
        return templates.TemplateResponse('sign-up/index.html', context={'request': request, 'feedback': feedback})

    with virtuoso.Session(URI) as session:
        if virtuoso.user.exists(session, email):
            feedback = 'Email already exists'
            return templates.TemplateResponse('sign-up/index.html', context={'request': request, 'feedback': feedback})

        virtuoso.user.create(session, fName, lName, email, hash_password(password))
    feedback = 'User successfully created'
    return templates.TemplateResponse('sign-in/index.html', context={'request': request, 'feedback': feedback})


@app.get('/login')
async def login(request: Request, response: Response, sessionID: Optional[str] = Cookie(None)):
    if sessionID:
        return RedirectResponse(url=app.url_path_for('browse'))

    return templates.TemplateResponse('sign-in/index.html', context={'request': request})


@app.post('/login')
async def login(request: Request, response: Response, email: str = Form(...), password: str = Form(...)):
    with virtuoso.Session(URI) as session:
        profile = virtuoso.user.from_email(session, email)
    profile = profile[0]
    db_password = profile['password']
    io_password = hash_password(password)

    if db_password != io_password:
        feedback = 'Incorrect e-mail or password'
        return templates.TemplateResponse('sign-in/index.html', context={'request': request, 'feedback': feedback})

    uid = str(uuid.uuid4())
    query = """
    insert in graph <http://www.securesea.ca/conupedia/user/> {
        <%s> sso:hasSession "%s" .
    }
    """ % (profile['user'], uid)
    with virtuoso.Session(URI) as session:
        session.post(query=query)

    response = RedirectResponse(url=app.url_path_for('browse'), status_code=status.HTTP_302_FOUND)
    response.set_cookie(key='sessionID', value=uid)
    response.set_cookie(key='profileID', value=str(re.sub('.*[/#]', '', profile['user'])))
    return response



@app.get('/logout')
async def logout(request: Request, sessionID: Optional[str] = Cookie(None)):
    if not sessionID:
        return RedirectResponse(url=app.url_path_for('login'))

    query = """
    with <http://www.securesea.ca/conupedia/user/> 
    delete { ?user sso:hasSession "%s" }
    where { ?user sso:hasSession "%s" }
    """ % (sessionID, sessionID)

    with virtuoso.Session(URI) as session:
        session.post(query=query)

    response = RedirectResponse(url=app.url_path_for('login'))
    response.delete_cookie(key='sessionID')
    response.delete_cookie(key='profileID')

    return response


@app.get('/browse')
async def browse(request: Request):

    return templates.TemplateResponse('dashboard/index.html', context={'request': request})


@app.get('/browse/{category}')
async def browse(request: Request,
                 category: str,
                 sessionID: Optional[str] = Cookie(None),
                 profileID: Optional[str] = Cookie(None)):
    if not sessionID:
        return RedirectResponse(url=app.url_path_for('login'))

    session = virtuoso.Session(URI)

    if category == 'explore':
        query = """
        select ?course where {
         ?course a schema:Course .
         filter not exists { ssu:%s sso:saw ?course . }
        } order by rand() limit 20
        """ % profileID
        response = session.post(query=query)
        courses = [item['course'] for item in response]

    if category == 'my-list':
        query = """
        select ?course where {
        ssu:%s sso:likes ?course .
        }
        """ % sessionID
        response = session.post(query=query)
        courses = [item['course'] for item in response]

    session.close()
    return templates.TemplateResponse('dashboard/index.html', context={'request': request})


@app.post('/browse/{category}/{title}')
async def browse(request: Request):
    return templates.TemplateResponse('sign-in/index.html', context={'request': request})


@app.get('/title/{title}')
async def browse(request: Request):
    return templates.TemplateResponse('sign-in/index.html', context={'request': request})


if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=8085)
