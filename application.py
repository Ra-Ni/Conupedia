import atexit
import shlex
import subprocess
from configparser import ConfigParser, ExtendedInterpolation
import datetime
import re
from asyncio.log import logger
from typing import Optional

import paramiko
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
import web_tools
from password import hash_password
from virtuoso.namespace import PREFIX, SSU

app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
templates = Jinja2Templates(directory="web/")
app.mount('/web', StaticFiles(directory='web'), name='web')

URI = None
SSH_CLIENT = None


@app.get('/register')
def register(request: Request):
    return templates.TemplateResponse('portal/register.html', context={'request': request})


@app.post('/register')
def register(request: Request,
             fName: str = Form(...),
             lName: str = Form(...),
             email: str = Form(...),
             password: str = Form(...)
             ):

    with virtuoso.Session(URI) as session:
        if virtuoso.user.exists(session, email):
            email_feedback = 'Email already exists'
            return templates.TemplateResponse('portal/login.html',
                                              context={'request': request, 'email_feedback': email_feedback})

        virtuoso.user.create(session, fName, lName, email, hash_password(password))

    response = RedirectResponse(url=app.url_path_for('login'), status_code=status.HTTP_302_FOUND)
    return response


@app.get('/login')
async def login(request: Request, response: Response, sessionID: Optional[str] = Cookie(None)):
    if sessionID:
        return RedirectResponse(url=app.url_path_for('dashboard'))

    return templates.TemplateResponse('portal/login.html', context={'request': request})


@app.post('/login')
async def login(request: Request, response: Response, email: str = Form(...), password: str = Form(...)):
    context = {'request': request}
    session = virtuoso.Session(URI)
    profile = virtuoso.user.from_email(session, email)

    if not profile:
        context['email_feedback'] = " The email you entered isn't connected to an account. "
        return templates.TemplateResponse('portal/login.html', context=context)

    profile = profile[0]
    db_password = profile['password']
    io_password = hash_password(password)

    if db_password != io_password:
        context['password_feedback'] = " The password you entered is incorrect. "
        return templates.TemplateResponse('portal/login.html', context=context)

    uid = str(uuid.uuid4())
    query = """
    %s
    insert in graph <http://www.securesea.ca/conupedia/user/> {
        <%s> sso:hasSession "%s" .
    }
    """ % (PREFIX, profile['user'], uid)

    session.post(query=query)
    session.close()

    response = RedirectResponse(url=app.url_path_for('dashboard'), status_code=status.HTTP_302_FOUND)
    response.set_cookie(key='sessionID', value=uid)
    response.set_cookie(key='profileID', value=str(re.sub('.*[/#]', '', profile['user'])))
    return response



@app.get('/logout')
async def logout(request: Request, sessionID: Optional[str] = Cookie(None)):
    if not sessionID:
        return RedirectResponse(url=app.url_path_for('login'))

    query = """
    %s
    with %s
    delete { ?user sso:hasSession "%s" }
    where { ?user sso:hasSession "%s" }
    """ % (PREFIX, SSU, sessionID, sessionID)

    with virtuoso.Session(URI) as session:
        session.post(query=query)

    response = RedirectResponse(url=app.url_path_for('login'))
    response.delete_cookie(key='sessionID')
    response.delete_cookie(key='profileID')

    return response



@app.get('/dashboard')
async def dashboard(request: Request, sessionID: Optional[str] = Cookie(None)):
    if not sessionID:
        return RedirectResponse(url=app.url_path_for('login'))

    session = virtuoso.Session(URI)

    popular = virtuoso.course.topk(session)
    for item in popular:
        item['partOf'] = re.sub(r'.*[/#](.*)\.html', r'\1', item['partOf']).title()
        item['course'] = re.sub(r'.*[/#](.*)', r'\1', item['course'])
    latest = virtuoso.course.latest(session)

    for item in latest:
        item['partOf'] = re.sub(r'.*[/#](.*)\.html', r'\1', item['partOf']).title()
        item['course'] = re.sub(r'.*[/#](.*)', r'\1', item['course'])

    user = virtuoso.user.from_token(session, sessionID)
    user = re.sub(r'.*[/#]', r'', user)
    explore = virtuoso.course.explore(session, user)
    session.close()
    context = {'request': request, 'popular': popular, 'latest': latest, 'explore': explore}
    return templates.TemplateResponse('student/dashboard.html', context=context)

@app.post('/user/{uid}/setThumbRating')
def set_thumb_rating(cid: str,
                 action: str = Form(...),
                 overwrite: str = Form(...),
                 sessionID: Optional[str] = Cookie(None)):
    if not sessionID:
        return RedirectResponse(url=app.url_path_for('login'), status_code=status.HTTP_302_FOUND)

    session = virtuoso.Session(URI)
    user = virtuoso.user.from_token(session, sessionID)
    user = re.sub(r'.*[/#]', '', user)

    if overwrite:
        virtuoso.user.revert_actions(session, user, cid)

    if action in ['like', 'dislike']:
        action += 's'
        virtuoso.user.insert(session, user, action, cid)

    session.close()

@app.post('/course/{cid}')
async def course(cid: str,
                 action: str = Form(...),
                 overwrite: str = Form(...),
                 sessionID: Optional[str] = Cookie(None)):
    if not sessionID:
        return RedirectResponse(url=app.url_path_for('login'), status_code=status.HTTP_302_FOUND)

    session = virtuoso.Session(URI)
    user = virtuoso.user.from_token(session, sessionID)
    user = re.sub(r'.*[/#]', '', user)

    if overwrite:
        virtuoso.user.revert_actions(session, user, cid)

    if action in ['like', 'dislike']:
        action += 's'
        virtuoso.user.insert(session, user, action, cid)


    session.close()

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

@atexit.register
def exit():
    SSH_CLIENT.terminate()

if __name__ == '__main__':
    config = ConfigParser(interpolation=ExtendedInterpolation())
    config.read('config.ini')
    sparql = config['Sparql']
    ssh = config['SSH']

    URI = sparql['CanonicalPath']

    command = 'ssh -L {}:{}:{} {}'.format(sparql['Port'],
                                          ssh['HostName'],
                                          sparql['Port'],
                                          ssh['Host'])
    command = shlex.split(command)
    SSH_CLIENT = subprocess.Popen(command) # stdout=subprocess.DEVNULL)
    uvicorn.run(app, host="0.0.0.0", port=8080)
