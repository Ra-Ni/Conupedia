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
from virtuoso import UserManager, Authenticator, CourseManager
from virtuoso.link import LinkManager
from virtuoso.namespace import SSC, SSO

app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
templates = Jinja2Templates(directory="web/")
app.mount('/web', StaticFiles(directory='web'), name='web')

URI = None
SESSION = None
user_manager = None
authenticator = None
link_manager = None
course_manager = None

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

    user = link_manager.get(None, 'foaf:mbox', f'"{email}"')
    if user:
        email_feedback = 'Email already exists'
        return templates.TemplateResponse('signup.html',
                                          context={'request': request, 'email_feedback': email_feedback})

    user_manager.add(fName, lName, email, hash_password(password))

    return RedirectResponse(url=app.url_path_for('login'), status_code=status.HTTP_302_FOUND)


@app.get('/login')
async def login(request: Request, response: Response, sessionID: Optional[str] = Cookie(None)):

    if sessionID:
        return RedirectResponse(url=app.url_path_for('dashboard'))

    return templates.TemplateResponse('login.html', context={'request': request})


@app.post('/login')
async def login(request: Request, response: Response, email: str = Form(...), password: str = Form(...)):
    context = {'request': request}
    user = link_manager.get(None, 'foaf:mbox', f'"{email}"')

    if not user:
        context['email_feedback'] = " The email you entered isn't connected to an account. "
        return templates.TemplateResponse('login.html', context=context)

    user_uri = '<' + user[0]['subject'] + '>'
    user = user_manager.get(user_uri, True)
    db_password = user['accessCode'][0]
    form_password = hash_password(password)

    if db_password != form_password:
        context['password_feedback'] = " The password you entered is incorrect. "
        return templates.TemplateResponse('login.html', context=context)

    token = authenticator.add(user_uri)

    response = RedirectResponse(url=app.url_path_for('dashboard'), status_code=status.HTTP_302_FOUND)
    response.set_cookie(key='sessionID', value=token)
    return response


@app.get('/logout')
async def logout(request: Request, sessionID: Optional[str] = Cookie(None)):
    if not sessionID:
        return RedirectResponse(url=app.url_path_for('login'))

    authenticator.delete(sessionID)

    response = RedirectResponse(url=app.url_path_for('login'))
    response.delete_cookie(key='sessionID')

    return response


@app.get('/dashboard')
async def dashboard(request: Request, sessionID: Optional[str] = Cookie(None)):
    if not sessionID:
        return RedirectResponse(url=app.url_path_for('login'))

    categories = dict()
    user_uri = authenticator.get(sessionID)
    user = user_manager.get(user_uri, True)

    categories['Recommended'] = course_manager.recommend(user_uri)
    categories['Popular'] = course_manager.popular()
    categories['Latest'] = course_manager.latest(user_uri)
    categories['Explore'] = course_manager.explore(user_uri)
    categories['Likes'] = course_manager.get(user_uri, 'likes')

    context = {'request': request,
               'categories': categories,
               'user_info': user}
    return templates.TemplateResponse('dashboard.html', context=context)


@app.get('/rating')
async def rating(id: str, sessionID: Optional[str] = Cookie(None)):
    if not sessionID:
        return RedirectResponse(url=app.url_path_for('login'))

    course = SSC[:-1] + f'{id}>'
    user = authenticator.get(sessionID)
    rating = link_manager.get(user, None, course)
    if not rating:
        return ''
    rating = re.sub(r'.*[/#]', '', rating[0]['key'])
    rating = rating[:-1]
    return rating

    # course_manager.get()
    #
    # user = virtuoso.user.from_token(SESSION, sessionID)
    # user = re.sub(r'.*[/#]', '', user)
    # retval = virtuoso.course.rating(SESSION, user, cuid)
    # return retval


@app.post('/rating')
async def course(cid: str = Form(...),
                 value: str = Form(...),
                 sessionID: Optional[str] = Cookie(None)):
    if not sessionID:
        return RedirectResponse(url=app.url_path_for('login'), status_code=status.HTTP_302_FOUND)

    course = SSC[:-1] + f'{cid}>'
    user = authenticator.get(sessionID)
    db_rating = link_manager.get(user, None, course)


    if db_rating:
        db_rating = db_rating[0]['key']
        link_manager.delete(user, '<' + db_rating + '>', course)
        db_rating = re.sub(r'.*[/#](.*)s', r'\1', db_rating)


    if value == db_rating:
        return

    link_manager.add(user, SSO[:-1] + f'{value}s>', course)


    #
    #
    #
    # user = virtuoso.user.from_token(SESSION, sessionID)
    # user = re.sub(r'.*[/#]', '', user)
    # db_rating = virtuoso.course.rating(SESSION, user, cuid)
    #
    # virtuoso.course.remove_rating(SESSION, user, cuid)
    # if rating == str(db_rating):
    #     return
    #
    # virtuoso.course.add_rating(SESSION, user, cuid, rating)


@app.get('/profile')
async def profile(request: Request, sessionID: Optional[str] = Cookie(None), profileID: Optional[str] = Cookie(None)):
    if not sessionID:
        return RedirectResponse(url=app.url_path_for('login'), status_code=status.HTTP_302_FOUND)

    user = authenticator.get(sessionID)
    user = user_manager.get(user, True)

    return templates.TemplateResponse('setting.html', context={'request': request, 'user_info': user})


@app.post('/profile')
async def profile(request: Request,
                  sessionID: Optional[str] = Cookie(None)):
    if not sessionID:
        return RedirectResponse(url=app.url_path_for('login'), status_code=status.HTTP_302_FOUND)

    return RedirectResponse(url=app.url_path_for('dashboard'), status_code=status.HTTP_302_FOUND)




if __name__ == '__main__':
    config = ConfigParser(interpolation=ExtendedInterpolation())
    config.read('config.ini')

    sparql = config['Sparql']
    URI = f'http://{sparql["IP"]}:{sparql["Port"]}{sparql["RelativePath"]}'
    SESSION = virtuoso.Session(URI)

    user_manager = UserManager(SESSION)
    authenticator = Authenticator(SESSION)
    link_manager = LinkManager(SESSION)
    course_manager = CourseManager(SESSION)
    server = config['Uvicorn']
    uvicorn.run(app, host=server['IP'], port=int(server['Port']))
