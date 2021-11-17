import datetime

import requests
from fastapi import FastAPI, Form, Request, Depends, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.security import OAuth2PasswordBearer
from fastapi.staticfiles import StaticFiles
import uuid

import virtuoso

app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
templates = Jinja2Templates(directory="web/")
app.mount('/web', StaticFiles(directory='web'), name='web')
URI = 'http://192.168.0.4:8890'


@app.get('/register')
def register(request: Request):
    result = 'type a username'
    return templates.TemplateResponse('sign-in/index.html', context={'request': request, 'result': result})

@app.post('/register')
async def register(request: Request, email: str = Form(...), password: str = Form(...)):
    result = email
    return templates.TemplateResponse('sign-in/index.html', context={'request': request, 'result': result})

@app.get('/login')
async def login(request: Request):
    return templates.TemplateResponse('sign-in/index.html', context={'request': request})

@app.post('/login')
async def login(request: Request, email: str = Form(...), password: str = Form(...)):
    with virtuoso.Session(URI) as session:
        user = virtuoso.user.from_email(session, email)

    result = user
    return templates.TemplateResponse('sign-in/index.html', context={'request': request, 'result': result})

@app.get('/browse')
async def browse(request: Request):
    return templates.TemplateResponse('sign-in/index.html', context={'request': request})

@app.get('/browse/{category}')
async def browse(request: Request):
    return templates.TemplateResponse('sign-in/index.html', context={'request': request})

@app.post('/browse/{category}/{title}')
async def browse(request: Request):
    return templates.TemplateResponse('sign-in/index.html', context={'request': request})

@app.get('/title/{title}')
async def browse(request: Request):
    return templates.TemplateResponse('sign-in/index.html', context={'request': request})

