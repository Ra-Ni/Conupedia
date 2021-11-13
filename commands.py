import datetime

import requests
from fastapi import FastAPI, Form, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
import uuid

import virtuoso

app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

URI = 'http://192.168.0.4:8890'


def hash_password(password: str) -> str:
    return password
    # h = sha256()
    # h.update(password.encode())
    # return h.hexdigest()


def get_username(token: str) -> str:
    query = """
    insert ?username {
        ?username 
    }
    """


def token_of(username: str) -> str:
    query = """
    select ?uid ?token ?expiry_date where {
        graph <http://www.securesea.ca/conupedia/token/> {
            ?uid a sso:Token ;
                rdf:value ?token ;
                sso:expires ?expiry_date ; 
                rdfs:seeAlso ssu:%s .
        }
    }
    """ % username
    with virtuoso.session() as session:
        response = virtuoso.post(URI, query, session)

    if not response:
        raise HTTPException(status_code=503, detail="Server Unavailable")

    response = response['results']['bindings']
    if not response:
        raise HTTPException(status_code=403, detail="Access Denied")

    response = response[0]
    uid = response['uid']['value']
    token = response['token']['value']
    expiry_date = response['expiry_date']['value']

    current_date = str(datetime.datetime.now().replace(microsecond=0))
    if current_date > expiry_date:
        query = """
        delete where {
            graph <http://www.securesea.ca/conupedia/token/> {
                <%s> ?p ?o .
            }
        }
        """ % uid
        with virtuoso.session() as session:
            response = virtuoso.post(URI, query, session)

        raise HTTPException(status_code=403, detail="Session Expired")

    return token

def create_token(username: str, session: requests.Session) -> dict:
    uid = uuid.uuid4()
    expiry_date = str(datetime.datetime.now().replace(microsecond=0))
    query = """
        insert in graph <http://www.securesea.ca/conupedia/token/> {
        sst:%s a sso:Token ;
            sso:expires "%s" ;
            rdfs:seeAlso ssu:%s .
        }
    """ % (uid, expiry_date, username)
    return virtuoso.post(URI, query, session)

def delete_tokens(username: str, session: requests.Session):
    query = """
       delete where {
           graph <http://www.securesea.ca/conupedia/token/> {
               ?s rdfs:seeAlso ssu:%s ;
                ?p ?o .
           }
       }
    """ % username
    session.post(URI, query, session)

def delete_token(uid: str, session: requests.Session):
    query = """
        delete where {
           graph <http://www.securesea.ca/conupedia/token/> {
               sst:%s ?p ?o .
           }
        }
        """ % uid
    session.post(URI, query, session)

def exists_token(username: str, session: requests.Session) -> bool:
    query = """
    select ?token where {
        graph <http://www.securesea.ca/conupedia/token/> {
            [] a sso:Token ;
                rdf:value ?token ; 
                rdfs:seeAlso ssu:%s .
        }
    }
    """
    response = virtuoso.post(URI, query, session)
    return response and response['results']['bindings']



def renew_token(validate=False):
    if validate:

@app.get('/')
def root():
    return {}


@app.post('/register')
async def register(username: str = Form(...),
                   password: str = Form(...),
                   fName: str = Form(...),
                   lName: str = Form(...),
                   email: str = Form(...)):
    query = """
    select ?user where {
        ?user rdfs:subClassOf foaf:Person .
        FILTER(?user = ssu:%s) .
    }
    """ % username
    with virtuoso.session() as session:
        response = virtuoso.post(URI, query, session)

    if not response:
        raise HTTPException(status_code=503, detail="Server Unavailable")

    if response['results']['bindings']:
        raise HTTPException(status_code=406, detail="Username already exists")

    queries = ["""
        insert in graph <http://www.securesea.ca/conupedia/user/> {
        ssu:%s a rdfs:Class ;
            rdfs:subClassOf foaf:Person ;
            foaf:firstName "%s" ;
            foaf:lastName "%s" ;
            foaf:mbox "%s" ;
            schema:accessCode "%s" .
        } 
        """ % (username, fName, lName, email, password), """
        insert in graph <http://www.securesea.ca/conupedia/token/> {
        sst:%s a sso:Token ;
            sso:expires "%s" ;
            rdfs:seeAlso ssu:%s .
        }
        """ % (f'{uuid.uuid4()}', f'{datetime.datetime.now().replace(microsecond=0)}', username)]

    with virtuoso.session() as session:
        for query in queries:
            virtuoso.post(URI, query, session)


@app.post('/login/')
async def login(username: str = Form(...), password: str = Form(...)):
    query = """
    select ?password where {
        ssu:%s schema:accessCode ?password . 
    }
    """ % username
    with virtuoso.session() as session:
        response = virtuoso.post(URI, query, session)

    if not response:
        raise HTTPException(status_code=400, detail="Incorrect username or password")

    db_credentials = response['results']['bindings']

    if not db_credentials:
        raise HTTPException(status_code=400, detail="Incorrect username or password")

    db_credentials = db_credentials[0]['password']['value']
    hashed_password = hash_password(password)

    print(f'{hashed_password} and {db_credentials}')
    if db_credentials != hashed_password:
        raise HTTPException(status_code=400, detail="Incorrect username or password")

    return {'access_token': username, 'token_type': 'bearer'}


@app.get("/items/")
async def read_items(token: str = Depends(oauth2_scheme)):
    return {"token": token}


@app.get('/users')
def list_user():
    return {}


@app.get('/courses')
async def courses():
    return {}


@app.get('/users/{uid}')
def get_user(uid: int):
    return {}


@app.get('/users/{uid}/courses')
def get_user_courses(uid: int):
    return {}


@app.get('/user/{uid}/courses/{cid}')
def get_user_course(uid: int, cid: int):
    return {}
