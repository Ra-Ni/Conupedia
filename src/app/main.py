import json
from typing import Optional
import fastapi
from fastapi import FastAPI, Request, Cookie, Response
from fastapi.staticfiles import StaticFiles
from starlette import status
from starlette.responses import RedirectResponse

from .dependencies import auth
from .dependencies.auth import InvalidCredentials
from .internals.globals import WEB_ASSETS, TEMPLATES
from .routers import signup, login, logout, profile, rating, admin, course
from .routers.rating import InvalidCourse

app = FastAPI()  # docs_url=None, openapi_url=None, redoc_url=None)
app.mount('/assets', StaticFiles(directory=WEB_ASSETS), name='assets')

app.include_router(signup.router)
app.include_router(login.router)
app.include_router(logout.router)
app.include_router(profile.router)
app.include_router(rating.router)
app.include_router(admin.router)
app.include_router(course.router)


@app.middleware("http")
async def authenticate(request: Request, call_next):
    cookies = request.cookies
    if 'token' not in cookies:
        if request.url.path not in ['/course', '/rating', '/']:
            response = await call_next(request)
            return response
        return RedirectResponse(url='/login', status_code=status.HTTP_302_FOUND)

    token = cookies['token']
    response = await auth.get(token)
    if response.status_code != status.HTTP_200_OK:
        response = RedirectResponse(url='/login', status_code=status.HTTP_302_FOUND)
        response.delete_cookie('token')
        return response

    request.state.user = response.background
    response = await call_next(request)

    return response


@app.get('/')
async def root(request: Request):
    user_profile = request.state.user
    response = await course.get_explore()
    response = json.loads(response.body)
    context = {'request': request, 'items': response, 'title': 'Explore', 'user_profile': user_profile}

    return TEMPLATES.TemplateResponse('course.html', context=context)


@app.exception_handler(InvalidCredentials)
def invalid_exception(response: Response, token: Optional[Cookie] = None):
    response = RedirectResponse(url='/login', status_code=status.HTTP_302_FOUND)
    response.delete_cookie('token')
    return response


@app.exception_handler(InvalidCourse)
def course_exception(request: Request, response: Response):
    return RedirectResponse(url=app.url_path_for('dashboard'), status_code=status.HTTP_302_FOUND)


@app.exception_handler(fastapi.exceptions.RequestValidationError)
def request_exception(request: Request, response: Response):
    return RedirectResponse(url=app.url_path_for('login'), status_code=status.HTTP_302_FOUND)

#
# @app.exception_handler(fastapi.exceptions.HTTPException)
# def http_exception(request: Request, response: Response):
#     return RedirectResponse(url=app.url_path_for('login'), status_code=status.HTTP_302_FOUND)
#
#
# @app.exception_handler(fastapi.exceptions.ValidationError)
# def validation_exception(request: Request, response: Response):
#     return RedirectResponse(url=app.url_path_for('login'), status_code=status.HTTP_302_FOUND)
#
#
# @app.exception_handler(StarletteHTTPException)
# def starlette_exception(request: Request, response: Response):
#     return RedirectResponse(url=app.url_path_for('login'), status_code=status.HTTP_302_FOUND)
#
#
