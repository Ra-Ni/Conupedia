from typing import Optional

import fastapi
from fastapi import FastAPI, Request, Cookie, Response
from fastapi.security import OAuth2PasswordBearer
from fastapi.staticfiles import StaticFiles
from starlette import status
from starlette.responses import RedirectResponse

from .dependencies.auth import InvalidCredentials
from .routers import signup, login, logout, profile, rating, dashboard
from .routers.rating import InvalidCourse

app = FastAPI(docs_url=None, openapi_url=None, redoc_url=None)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
app.mount('/web', StaticFiles(directory='app/web'), name='web')

app.include_router(signup.router)
app.include_router(login.router)
app.include_router(logout.router)
app.include_router(profile.router)
app.include_router(rating.router)
app.include_router(dashboard.router)


@app.get('/')
async def root():
    return RedirectResponse(url=app.url_path_for('dashboard'))


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
# if __name__ == '__main__':
#     config = ConfigParser(interpolation=ExtendedInterpolation())
#     config.read('config.ini')
#
#     sparql = config['Sparql']
#     URI = f'http://{sparql["IP"]}:{sparql["Port"]}'
#     PATH = sparql["RelativePath"]
#
#     server = config['Uvicorn']
#     uvicorn.run(app, host=server['IP'], port=int(server['Port']))