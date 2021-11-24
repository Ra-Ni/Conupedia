import uuid
from configparser import ConfigParser, ExtendedInterpolation
import re
from io import StringIO
from typing import Optional

import httpx
import pandas as pd
import shortuuid
import uvicorn
from fastapi import FastAPI, Form, Request, Response, Cookie
from fastapi.templating import Jinja2Templates
from fastapi.security import OAuth2PasswordBearer
from fastapi.staticfiles import StaticFiles

from starlette import status
from starlette.responses import RedirectResponse

from password import hash_password

from virtuoso.namespace import ssu, sso, prefix, reverse_namespaces, sst, ssc

app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
templates = Jinja2Templates(directory="web/")
app.mount('/web', StaticFiles(directory='web'), name='web')

URI = None
PATH = None

session = None


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
    query = """
    ask from %s { ?s foaf:mbox "%s" }
    """ % (ssu, email)
    query = build(query)

    async with httpx.AsyncClient(base_url=URI) as client:
        response = await client.get(PATH, params=query)
        response = to_frame(response)
        exists = bool(response.iat[0, 0])

        if exists:
            email_feedback = 'Email already exists'
            return templates.TemplateResponse('signup.html',
                                              context={'request': request, 'email_feedback': email_feedback})

        uid = shortuuid.uuid()
        query = """
        insert in graph %s {
            ssu:%s a foaf:Person ;
                rdfs:label "%s" ; 
                foaf:firstName "%s" ;
                foaf:lastName "%s" ;
                foaf:mbox "%s" ;
                schema:accessCode "%s" ;
                sso:status "active" .
        }
        """ % (ssu, uid, uid, fName, lName, email, hash_password(password))
        query = build(query)
        response = await client.get(PATH, params=query)
        print(response)

    return RedirectResponse(url=app.url_path_for('login'), status_code=status.HTTP_302_FOUND)


@app.get('/login')
async def login(request: Request, response: Response, sessionID: Optional[str] = Cookie(None)):
    if sessionID:
        return RedirectResponse(url=app.url_path_for('dashboard'))

    return templates.TemplateResponse('login.html', context={'request': request})


@app.post('/login')
async def login(request: Request, response: Response, email: str = Form(...), password: str = Form(...)):
    context = {'request': request}
    query = """
    select ?user ?password 
    from %s
    where {
        ?user a foaf:Person ;
            foaf:mbox "%s" ;
            schema:accessCode ?password .
    }
    """ % (ssu, email)
    query = build(query)
    async with httpx.AsyncClient(base_url=URI) as client:
        response = await client.get(PATH, params=query)
        response = to_frame(response)

        if response.empty:
            context['email_feedback'] = " The email you entered isn't connected to an account. "
            return templates.TemplateResponse('login.html', context=context)

        user = response.iat[0, 0]
        db_password = response.iat[0, 1]

        if db_password != hash_password(password):
            context['password_feedback'] = " The password you entered is incorrect. "
            return templates.TemplateResponse('login.html', context=context)

        tid = shortuuid.uuid()
        token = uuid.uuid4().hex + uuid.uuid4().hex
        query = """
        insert in graph %s {
            sst:%s a sso:Token ;
                rdfs:label "%s" ;
                rdf:value "%s" ;
                rdfs:seeAlso %s .
        } 
        """ % (sst, tid, tid, token, user)
        query = build(query)
        response = await client.get(PATH, params=query)

    response = RedirectResponse(url=app.url_path_for('login'), status_code=status.HTTP_302_FOUND)
    response.set_cookie('sessionID', token)
    return response


@app.get('/logout')
async def logout(request: Request, sessionID: Optional[str] = Cookie(None)):
    if not sessionID:
        return RedirectResponse(url=app.url_path_for('login'))

    query = """
    delete { ?s ?p ?o }
    where { 
        graph %s {
            ?s a sso:Token ;
                rdf:value "%s" ;
                ?p ?o .
        }
    } 
    """ % (sst, sessionID)
    query = build(query)
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
    query = """
    select ?id ?firstName ?lastName ?mbox
    where {
        graph %s {
            [] a sso:Token ;
                rdfs:seeAlso ?id ;
                rdf:value "%s" .
        }
        graph %s {
            ?id foaf:firstName ?firstName ;
                foaf:lastName ?lastName ;
                foaf:mbox ?mbox .
        }
    }
    """ % (sst, sessionID, ssu)
    query = build(query)

    async with httpx.AsyncClient(base_url=URI) as client:
        user = await client.get(PATH, params=query)
        user = to_frame(user)
        context['user_info'] = user = user.to_dict('records')[0]

        methods = {
            'Recommended': recommend,
            'Popular': get_popular,
            'Explore': get_explore,
            'Latest': get_latest,
            'Likes': likes,
        }
        for title, method in methods.items():
            query = method(user['id'])
            latest = await client.get(PATH, params=query)
            latest = to_frame(latest)
            context['categories'][title] = latest.to_dict('records')

    return templates.TemplateResponse('dashboard.html', context=context)


def get_popular(user: str, threshold: int = 50):
    query = """
    select ?course ?code ?title ?credits ?partOf ?description 
    where {
        ?c a schema:Course ;
            rdfs:label ?course ;
            schema:courseCode ?code ;
            schema:name ?title ;
            schema:numberOfCredits ?credits ;
            schema:isPartOf ?partOf ;
            schema:description ?description .
        {
            select ?c (count(?c) as ?count)
            where { [] sso:likes ?c .} 
            group by ?c 
            order by desc(?count)
            limit %s
        }
    }
    """ % threshold

    return build(query)


def get_latest(user: str, threshold: int = 50):
    query = """
    select *
    where {
    ?c a schema:Course ;
        rdfs:label ?course ;
        schema:courseCode ?code ;
        schema:name ?title ;
        schema:numberOfCredits ?credits ;
        schema:isPartOf ?partOf ;
        schema:description ?description ;
        schema:dateCreated ?date .
    filter not exists { %s [] ?c }
    } 
    order by desc(?date) 
    limit %s 
    """ % (user, threshold)

    return build(query)


def get_explore(user: str, threshold: int = 50):
    query = """
    select ?course ?code ?title ?credits ?partOf ?description
    where {
    ?c a schema:Course ;
        rdfs:label ?course ;
        schema:courseCode ?code ;
        schema:name ?title ;
        schema:numberOfCredits ?credits ;
        schema:isPartOf ?partOf ;
        schema:description ?description .
        filter not exists { %s [] ?c }
    } 
    order by rand()
    limit %s 
    """ % (user, threshold)

    return build(query)


def recommend(user: str, threshold: int = 50):
    query = """
    select distinct ?course ?code ?title ?credits ?partOf ?description 
    where {
        %s sso:likes ?o .
        ?o rdfs:seeAlso ?c .
        ?c  rdfs:label ?course ;
            schema:courseCode ?code ;
            schema:name ?title ;
            schema:numberOfCredits ?credits ;
            schema:isPartOf ?partOf ;
            schema:description ?description .
        filter not exists { %s [] ?c }
    } 
    group by ?course 
    order by rand()
    limit %s
    """ % (user, user, threshold)

    return build(query)


def likes(user: str, threshold: int = 50):
    query = """
    select distinct ?course ?code ?title ?credits ?partOf ?description
    where {
        %s sso:likes ?c .
        ?c  rdfs:label ?course ;
            schema:courseCode ?code ;
            schema:name ?title ;
            schema:numberOfCredits ?credits ;
            schema:isPartOf ?partOf ;
            schema:description ?description .
    }
    """ % user

    return build(query)


@app.get('/rating')
async def rating(id: str, sessionID: Optional[str] = Cookie(None)):
    if not sessionID:
        return RedirectResponse(url=app.url_path_for('login'))

    query = """
    select ?reaction 
    where {
        graph %s {
            [] a sso:Token ;
                rdfs:seeAlso ?user ;
                rdf:value "%s" .
        }
        graph %s {
            values ?reaction { sso:likes sso:dislikes }
            ?user ?reaction ssc:%s .
        }
    }
    """ % (sst, sessionID, ssu, id.zfill(6))
    query = build(query)
    async with httpx.AsyncClient(base_url=URI) as client:

        reaction = await client.get(PATH, params=query)
        reaction = to_frame(reaction)

        if reaction.empty:
            return ''

        reaction = re.sub(r'.*:(.*).', r'\1', reaction.iat[0, 0])
        return reaction


@app.post('/rating')
async def course(cid: str = Form(...),
                 value: str = Form(...),
                 sessionID: Optional[str] = Cookie(None)):
    if not sessionID:
        return RedirectResponse(url=app.url_path_for('login'), status_code=status.HTTP_302_FOUND)

    value = f'sso:{value}s'
    course = f'ssc:{cid.zfill(6)}'
    query = """
    select ?user ?reaction {
        graph %s  {
            ?t a sso:Token ;
                rdfs:seeAlso ?user ;
                rdf:value "%s" .
        }
        optional {
            graph %s {
                values ?reaction { sso:likes sso:dislikes }
                 ?user ?reaction %s .
            }
        }
    }
    """ % (sst, sessionID, ssu, course)

    query = build(query)

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
    pass
    # if not sessionID:
    #     return RedirectResponse(url=app.url_path_for('login'), status_code=status.HTTP_302_FOUND)
    #
    # user = authenticator.get(sessionID)
    # user = user_manager.get(user, True)
    #
    # return templates.TemplateResponse('setting.html', context={'request': request, 'user_info': user})


@app.post('/profile')
async def profile(request: Request,
                  sessionID: Optional[str] = Cookie(None)):
    pass
    # if not sessionID:
    #     return RedirectResponse(url=app.url_path_for('login'), status_code=status.HTTP_302_FOUND)
    #
    # return RedirectResponse(url=app.url_path_for('dashboard'), status_code=status.HTTP_302_FOUND)


def build(query, **kwargs):
    query = f'{prefix}\n{query}'
    request = {
        'default-graph-uri': '',
        'query': query,
        'format': 'text/csv; charset=UTF-8',
        'should-sponge': '',
        'signal_void': 'on',
        'signal_unconnected': 'on',
        'timeout': '0',
    }

    request.update(kwargs)
    return request


def to_namespaces(resource):
    if not isinstance(resource, str):
        return resource

    match = re.match(r'http://.*[/#]', resource)

    if not match:
        return resource

    match = match.group()

    if match not in reverse_namespaces:
        return resource

    return resource.replace(match, f'{reverse_namespaces[match]}:')


def to_frame(response):
    if response.status_code == 400:
        raise AttributeError('Invalid Request')

    frame = pd.read_csv(StringIO(response.text))
    frame = frame.applymap(to_namespaces)
    return frame


async def _send_request(self, query, method):
    metadata = self._metadata.copy()
    metadata['query'] = query

    async with httpx.AsyncClient(base_url=self._base_url) as client:
        if method == 'get':
            response = await client.get(self._endpoint, params=metadata)

        elif method == 'post':
            response = await client.post(self._endpoint, data=metadata)

        else:
            raise NotImplementedError('No post or get method')

    if response.status_code == 400:
        raise AttributeError('Following query is not valid:\n%s' % query)

    frame = pd.read_csv(StringIO(response.text))
    frame = frame.applymap(to_namespaces)

    return frame


if __name__ == '__main__':
    config = ConfigParser(interpolation=ExtendedInterpolation())
    config.read('config.ini')

    sparql = config['Sparql']
    URI = f'http://{sparql["IP"]}:{sparql["Port"]}'
    PATH = sparql["RelativePath"]

    server = config['Uvicorn']
    uvicorn.run(app, host=server['IP'], port=int(server['Port']))
