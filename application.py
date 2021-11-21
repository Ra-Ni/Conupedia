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
SESSION = None


@app.get('/signup')
def signup(request: Request, sessionID: Optional[str] = Cookie(None)):
    if sessionID:
        return RedirectResponse(url=app.url_path_for('dashboard'))

    return templates.TemplateResponse('portal/signup.html', context={'request': request})


@app.post('/signup')
def signup(request: Request,
           fName: str = Form(...),
           lName: str = Form(...),
           email: str = Form(...),
           password: str = Form(...),
           sessionID: Optional[str] = Cookie(None)
           ):

    if virtuoso.user.exists(SESSION, email):
        email_feedback = 'Email already exists'
        return templates.TemplateResponse('portal/signup.html',
                                          context={'request': request, 'email_feedback': email_feedback})

    virtuoso.user.create(SESSION, fName, lName, email, hash_password(password))
    return RedirectResponse(url=app.url_path_for('login'), status_code=status.HTTP_302_FOUND)


@app.get('/login')
async def login(request: Request, response: Response, sessionID: Optional[str] = Cookie(None)):
    if sessionID:
        return RedirectResponse(url=app.url_path_for('dashboard'))

    return templates.TemplateResponse('portal/login.html', context={'request': request})


@app.post('/login')
async def login(request: Request, response: Response, email: str = Form(...), password: str = Form(...)):
    context = {'request': request}

    profile = virtuoso.user.from_email(SESSION, email)

    if not profile:
        context['email_feedback'] = " The email you entered isn't connected to an account. "
        return templates.TemplateResponse('portal/login.html', context=context)

    profile = profile[0]
    user = re.sub(r'.*[/#]', '', profile['user'])
    db_password = profile['password']
    io_password = hash_password(password)

    if db_password != io_password:
        context['password_feedback'] = " The password you entered is incorrect. "
        return templates.TemplateResponse('portal/login.html', context=context)

    virtuoso.authentication.delete(SESSION, user)
    token = virtuoso.authentication.create(SESSION, user=user)

    response = RedirectResponse(url=app.url_path_for('dashboard'), status_code=status.HTTP_302_FOUND)
    response.set_cookie(key='sessionID', value=token)
    response.set_cookie(key='profileID', value=user)
    return response


@app.get('/logout')
async def logout(request: Request, sessionID: Optional[str] = Cookie(None)):
    if not sessionID:
        return RedirectResponse(url=app.url_path_for('login'))

    virtuoso.authentication.delete(SESSION, token=sessionID)

    response = RedirectResponse(url=app.url_path_for('login'))
    response.delete_cookie(key='sessionID')
    response.delete_cookie(key='profileID')

    return response


@app.get('/dashboard')
async def dashboard(request: Request, sessionID: Optional[str] = Cookie(None)):
    if not sessionID:
        return RedirectResponse(url=app.url_path_for('login'))

    popular = virtuoso.course.popular(SESSION)
    latest = virtuoso.course.latest(SESSION)
    user = virtuoso.user.from_token(SESSION, sessionID)
    user = re.sub(r'.*[/#]', r'', user)
    explore = virtuoso.course.explore(SESSION, user)
    likes = virtuoso.course.get(SESSION, user, 'likes')
    context = {'request': request, 'popular': popular, 'latest': latest, 'explore': explore, 'likes': likes}
    return templates.TemplateResponse('student/dashboard.html', context=context)


@app.post('/course/{cid}')
async def course(cid: str,
                 action: str = Form(...),
                 overwrite: str = Form(...),
                 sessionID: Optional[str] = Cookie(None)):
    if not sessionID:
        return RedirectResponse(url=app.url_path_for('login'), status_code=status.HTTP_302_FOUND)

    user = virtuoso.user.from_token(SESSION, sessionID)
    user = re.sub(r'.*[/#]', '', user)

    if overwrite:
        virtuoso.user.revert_actions(SESSION, user, cid)

    if action in ['like', 'dislike']:
        action += 's'
        virtuoso.user.insert(SESSION, user, action, cid)


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
    SSH_CLIENT = subprocess.Popen(command)  # stdout=subprocess.DEVNULL)
    SESSION = virtuoso.Session(URI)
    uvicorn.run(app, host="127.0.0.1", port=8083)
