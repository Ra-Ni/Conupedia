import atexit
import shlex
import subprocess
from configparser import ConfigParser, ExtendedInterpolation
import re
from typing import Optional

import uvicorn
from fastapi import FastAPI, Form, Request, Response, Cookie
from fastapi.templating import Jinja2Templates
from fastapi.security import OAuth2PasswordBearer
from fastapi.staticfiles import StaticFiles

from starlette import status
from starlette.responses import RedirectResponse

import virtuoso
from password import hash_password


app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
templates = Jinja2Templates(directory="web/")
app.mount('/web', StaticFiles(directory='web'), name='web')

URI = None
SSH_CLIENT = None
SESSION = None


@app.get('/')
def root():
    return RedirectResponse(url=app.url_path_for('dashboard'))


@app.get('/signup')
def signup(request: Request, sessionID: Optional[str] = Cookie(None)):
    if sessionID:
        return RedirectResponse(url=app.url_path_for('dashboard'))

    return templates.TemplateResponse('signup.html', context={'request': request})


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
        return templates.TemplateResponse('signup.html',
                                          context={'request': request, 'email_feedback': email_feedback})

    virtuoso.user.create(SESSION, fName, lName, email, hash_password(password))
    return RedirectResponse(url=app.url_path_for('login'), status_code=status.HTTP_302_FOUND)


@app.get('/login')
async def login(request: Request, response: Response, sessionID: Optional[str] = Cookie(None)):
    if sessionID:
        return RedirectResponse(url=app.url_path_for('dashboard'))

    return templates.TemplateResponse('login.html', context={'request': request})


@app.post('/login')
async def login(request: Request, response: Response, email: str = Form(...), password: str = Form(...)):
    context = {'request': request}

    profile = virtuoso.user.from_email(SESSION, email)

    if not profile:
        context['email_feedback'] = " The email you entered isn't connected to an account. "
        return templates.TemplateResponse('login.html', context=context)

    profile = profile[0]
    user = re.sub(r'.*[/#]', '', profile['user'])
    db_password = profile['password']
    io_password = hash_password(password)

    if db_password != io_password:
        context['password_feedback'] = " The password you entered is incorrect. "
        return templates.TemplateResponse('login.html', context=context)

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

    categories = dict()
    user_info = virtuoso.user.basic_information(SESSION, sessionID)
    user = user_info['user']

    categories['Recommended'] = virtuoso.course.recommend(SESSION, user)
    categories['Popular'] = virtuoso.course.popular(SESSION)
    categories['Latest'] = virtuoso.course.latest(SESSION, user)
    categories['Explore'] = virtuoso.course.explore(SESSION, user)
    categories['Likes'] = virtuoso.course.get(SESSION, user, 'likes')

    context = {'request': request,
               'categories': categories,
               'user_info': user_info}
    return templates.TemplateResponse('dashboard.html', context=context)


@app.get('/course/{cuid}/rating')
async def rating(cuid: str, sessionID: Optional[str] = Cookie(None)):
    user = virtuoso.user.from_token(SESSION, sessionID)
    user = re.sub(r'.*[/#]', '', user)
    retval = virtuoso.course.rating(SESSION, user, cuid)
    return retval


@app.post('/course/{cuid}/rating')
async def course(cuid: str,
                 rating: str = Form(...),
                 sessionID: Optional[str] = Cookie(None)):
    if not sessionID:
        return RedirectResponse(url=app.url_path_for('login'), status_code=status.HTTP_302_FOUND)

    user = virtuoso.user.from_token(SESSION, sessionID)
    user = re.sub(r'.*[/#]', '', user)
    db_rating = virtuoso.course.rating(SESSION, user, cuid)

    virtuoso.course.remove_rating(SESSION, user, cuid)
    if rating == str(db_rating):
        return

    virtuoso.course.add_rating(SESSION, user, cuid, rating)



@app.get('/profile')
async def profile(request: Request, sessionID: Optional[str] = Cookie(None), profileID: Optional[str] = Cookie(None)):
    if not sessionID:
        return RedirectResponse(url=app.url_path_for('login'), status_code=status.HTTP_302_FOUND)
    user_info = virtuoso.user.basic_information(SESSION, sessionID)
    return templates.TemplateResponse('setting.html', context={'request': request, 'user_info': user_info})


@app.post('/profile')
async def profile(request: Request,
                  sessionID: Optional[str] = Cookie(None)):
    raise NotImplementedError()


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
