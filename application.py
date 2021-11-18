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
import web_tools
from password import hash_password

app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
templates = Jinja2Templates(directory="web/")
app.mount('/web', StaticFiles(directory='web'), name='web')
URI = 'http://192.168.0.4:8890/sparql'


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
    insert in graph <http://www.securesea.ca/conupedia/user/> {
        <%s> sso:hasSession "%s" .
    }
    """ % (profile['user'], uid)

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

    session.close()

    return templates.TemplateResponse('student/dashboard.html', context={'request': request, 'popular': popular, 'latest': latest})

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


if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=8086)
