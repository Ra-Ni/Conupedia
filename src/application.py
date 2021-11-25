from configparser import ConfigParser, ExtendedInterpolation
import re
from io import StringIO
from typing import Optional

import fastapi.exceptions
import httpx
import pandas as pd
import uvicorn
from fastapi import FastAPI, Form, Request, Response, Cookie
from fastapi.templating import Jinja2Templates
from fastapi.security import OAuth2PasswordBearer
from fastapi.staticfiles import StaticFiles

from starlette import status
from starlette.responses import RedirectResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

import virtuoso
from virtuoso import *
from virtuoso import auth, user
from virtuoso.namespace import ssu
from virtuoso.base import build, hash_password, to_frame

app = FastAPI(docs_url=None, openapi_url=None, redoc_url=None)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
templates = Jinja2Templates(directory="web/")
app.mount('/web', StaticFiles(directory='web'), name='web')


@app.get('/')
async def root():
    return RedirectResponse(url=app.url_path_for('dashboard'))


@app.get('/signup')
async def signup(request: Request, sessionID: Optional[str] = Cookie(None)):
    if sessionID:
        return RedirectResponse(url=app.url_path_for('dashboard'))

    return templates.TemplateResponse('signup.html', context={'request': request})


@app.post('/signup')
async def signup(request: Request,
                 fName: str = Form(...),
                 lName: str = Form(...),
                 email: str = Form(...),
                 password: str = Form(...),
                 sessionID: Optional[str] = Cookie(None)
                 ):
    query = user.exists_email(email)

    async with httpx.AsyncClient(base_url=URI) as client:
        response = await client.get(PATH, params=query)
        response = to_frame(response)
        exists = bool(response.iat[0, 0])

        if exists:
            email_feedback = 'Email already exists'
            return templates.TemplateResponse('signup.html',
                                              context={'request': request, 'email_feedback': email_feedback})

        query = user.new(fName, lName, email, password)
        await client.get(PATH, params=query)

    return RedirectResponse(url=app.url_path_for('login'), status_code=status.HTTP_302_FOUND)


@app.get('/login')
async def login(request: Request, response: Response, sessionID: Optional[str] = Cookie(None)):
    if sessionID:
        return RedirectResponse(url=app.url_path_for('dashboard'))

    return templates.TemplateResponse('login.html', context={'request': request})


@app.post('/login')
async def login(request: Request, response: Response, email: str = Form(...), password: str = Form(...)):
    context = {'request': request}
    query = virtuoso.user.from_email(email)

    async with httpx.AsyncClient(base_url=URI) as client:
        response = await client.get(PATH, params=query)
        response = to_frame(response)

        if response.empty:
            context['email_feedback'] = " The email you entered isn't connected to an account. "
            return templates.TemplateResponse('login.html', context=context)

        response = response.to_dict('records')[0]

        if response['password'] != hash_password(password):
            context['password_feedback'] = " The password you entered is incorrect. "
            return templates.TemplateResponse('login.html', context=context)

        query, token = auth.new(response['id'])
        await client.get(PATH, params=query)

    response = RedirectResponse(url=app.url_path_for('login'), status_code=status.HTTP_302_FOUND)
    response.set_cookie('sessionID', token)
    return response


@app.get('/logout')
async def logout(request: Request, sessionID: Optional[str] = Cookie(None)):
    if not sessionID:
        return RedirectResponse(url=app.url_path_for('login'))

    query = auth.delete(sessionID)
    async with httpx.AsyncClient(base_url=URI) as client:
        await client.get(PATH, params=query)

    response = RedirectResponse(url=app.url_path_for('login'))
    response.delete_cookie(key='sessionID')
    return response


@app.get('/dashboard')
async def dashboard(request: Request, sessionID: Optional[str] = Cookie(None)):
    if not sessionID:
        return RedirectResponse(url=app.url_path_for('login'))

    context = {'request': request, 'categories': {}}
    query = virtuoso.user.from_token(sessionID)

    async with httpx.AsyncClient(base_url=URI) as client:
        user = await client.get(PATH, params=query)
        user = to_frame(user)
        context['user_info'] = user = user.to_dict('records')[0]

        methods = {
            'Recommended': get_recommendation,
            'Popular': get_popular,
            'Explore': get_explore,
            'Latest': get_latest,
            'Likes': get_likes,
        }
        for title, method in methods.items():
            query = method(user['id'])

            latest = await client.get(PATH, params=query)
            latest = to_frame(latest)
            context['categories'][title] = latest.to_dict('records')

    return templates.TemplateResponse('dashboard.html', context=context)


@app.get('/rating')
async def rating(id: str, sessionID: Optional[str] = Cookie(None)):
    if not sessionID:
        return RedirectResponse(url=app.url_path_for('login'))

    id = f'ssc:{id.zfill(6)}'
    query = virtuoso.user.get_reaction(sessionID, id)

    async with httpx.AsyncClient(base_url=URI) as client:

        reaction = await client.get(PATH, params=query)
        reaction = to_frame(reaction)

        if reaction.empty or pd.isna(reaction.iat[0, 1]):
            return ''

        reaction = re.sub(r'.*:(.*).', r'\1', reaction.iat[0, 1])
        return reaction


@app.post('/rating')
async def rating(cid: str = Form(...),
                 value: str = Form(...),
                 sessionID: Optional[str] = Cookie(None)):
    if not sessionID:
        return RedirectResponse(url=app.url_path_for('login'), status_code=status.HTTP_302_FOUND)

    value = f'sso:{value}s'
    course = f'ssc:{cid.zfill(6)}'
    query = virtuoso.user.get_reaction(sessionID, course)

    async with httpx.AsyncClient(base_url=URI) as client:
        response = await client.get(PATH, params=query)
        response = to_frame(response)

        user = response.iat[0, 0]
        reaction = response.iat[0, 1]

        if reaction == value:
            insert = ''
        else:
            insert = f'{user} {value} {course}'

        if pd.notna(reaction):
            delete = f'{user} {reaction} {course}'
        else:
            delete = ''

        query = """
        modify %s
        delete {%s}
        insert {%s}
        """ % (ssu, delete, insert)
        query = build(query)
        response = await client.get(PATH, params=query)


@app.get('/profile')
async def profile(request: Request, sessionID: Optional[str] = Cookie(None), profileID: Optional[str] = Cookie(None)):
    if not sessionID:
        return RedirectResponse(url=app.url_path_for('login'), status_code=status.HTTP_302_FOUND)

    query = virtuoso.user.from_token(sessionID)
    context = {'request': request, 'user_info': None}

    async with httpx.AsyncClient(base_url=URI) as client:
        response = await client.get(PATH, params=query)
        response = to_frame(response)
        context['user_info'] = response.to_dict('records')[0]

    return templates.TemplateResponse('setting.html', context=context)


@app.post('/profile')
async def profile(request: Request,
                  current_password: str = Form(...),
                  new_password: str = Form(...),
                  confirm_new_password: str = Form(...),
                  sessionID: Optional[str] = Cookie(None)):
    if not sessionID:
        return RedirectResponse(url=app.url_path_for('login'), status_code=status.HTTP_302_FOUND)
    context = {'request': request, 'password_feedback': None}

    if new_password != confirm_new_password:
        context['password_error'] = "Passwords do not match."
        return templates.TemplateResponse('setting.html', context=context)

    query = user.from_token(sessionID)
    async with httpx.AsyncClient(base_url=URI) as client:
        response = await client.get(PATH, params=query)
        response = to_frame(response)
        credentials = context['user_info'] = response.to_dict('records')[0]

        if credentials['password'] != hash_password(current_password):
            context['password_error'] = "Incorrect input for current password."
            return templates.TemplateResponse('setting.html', context=context)

        query = user.update_password(sessionID, new_password)
        response = await client.get(PATH, params=query)

    context['password_feedback'] = "Password updated successfully."
    return templates.TemplateResponse('setting.html', context=context)


@app.exception_handler(fastapi.exceptions.HTTPException)
def http_exception(request: Request, response: Response):
    return RedirectResponse(url=app.url_path_for('login'), status_code=status.HTTP_302_FOUND)


@app.exception_handler(fastapi.exceptions.ValidationError)
def validation_exception(request: Request, response: Response):
    return RedirectResponse(url=app.url_path_for('login'), status_code=status.HTTP_302_FOUND)


@app.exception_handler(StarletteHTTPException)
def starlette_exception(request: Request, response: Response):
    return RedirectResponse(url=app.url_path_for('login'), status_code=status.HTTP_302_FOUND)


@app.exception_handler(fastapi.exceptions.RequestValidationError)
def request_exception(request: Request, response: Response):
    return RedirectResponse(url=app.url_path_for('login'), status_code=status.HTTP_302_FOUND)


if __name__ == '__main__':
    config = ConfigParser(interpolation=ExtendedInterpolation())
    config.read('config.ini')

    sparql = config['Sparql']
    URI = f'http://{sparql["IP"]}:{sparql["Port"]}'
    PATH = sparql["RelativePath"]

    server = config['Uvicorn']
    uvicorn.run(app, host=server['IP'], port=int(server['Port']))
