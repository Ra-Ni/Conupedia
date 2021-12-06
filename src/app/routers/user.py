from typing import Optional

import httpx
import shortuuid
from fastapi import Response
from fastapi.encoders import jsonable_encoder
from starlette import status
from starlette.responses import JSONResponse
from ..dependencies import core
from ..internals.globals import SSU


class Term:
    def __init__(self, predicate, value, type= str):
        self.predicate = predicate
        self.value = value
        self.type = type

    def __str__(self):
        if not self.value:
            return ''

        if ':' in self.value or self.value.startswith('?'):
            value = f'{self.value}'
        else:
            value = f'"{self.value}"'
            if self.type == float:
                value += '^^xsd:float'

        return f'{self.predicate} {value}'

    def empty(self):
        return not self.value


class User:
    def __init__(self, id: Optional[str] = None,
                 label: Optional[str] = None,
                 first_name: Optional[str] = None,
                 last_name: Optional[str] = None,
                 email: Optional[str] = None,
                 password: Optional[str] = None,
                 status: Optional[str] = None):
        self.id = id
        self.type = Term('a', 'foaf:Person')
        self.label = Term('rdfs:label', label)
        self.first_name = Term('foaf:firstName', first_name)
        self.last_name = Term('foaf:lastName', last_name)
        self.email = Term('foaf:mbox', email)
        self.password = Term('schema:accessCode', password)
        self.status = Term('sso:status', status)

    def to_rdf(self):
        rdf = [str(v) for v in self.__dict__.values() if isinstance(v, Term) and not v.empty()]

        if not self.id:
            id = '[]'
        elif not self.id.startswith('?'):
            id = f'ssu:{self.id}'
        else:
            id = self.id

        return id + ' ' + ';'.join(rdf) + '.'

    @classmethod
    def query(cls):
        return User(label='?id',
                    first_name='?firstName',
                    last_name='?lastName',
                    email='?email',
                    password='?password',
                    status='?status')


async def get_user(id: str):
    query = """
    with %s
    select ?id ?firstName ?lastName ?email ?password ?status
    where { 
        %s
        filter (?id = "%s")
    } 
    """ % (SSU, User.query().to_rdf(), id)
    async with httpx.AsyncClient() as client:
        response = await core.send(client, query, 'dict')

    if not response:
        return Response(status_code=status.HTTP_404_NOT_FOUND)

    return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder(response))


async def get(email: str):
    query = """
    select *
    where {
        graph %s {
            [] a foaf:Person ;
                rdfs:label ?id ; 
                foaf:firstName ?first_name ;
                foaf:lastName ?last_name ;
                foaf:mbox ?email ;
                schema:accessCode ?password ;
                sso:status ?status .
            filter ("%s" = ?email)
        }
    }
    """ % (SSU, email)
    async with httpx.AsyncClient() as client:
        response = await core.send(client, query, format='dict')

        if response:
            return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder(response))

    return Response(status_code=status.HTTP_404_NOT_FOUND)


async def post(email: str, password: str, first_name: str, last_name: str):
    uid = shortuuid.uuid()
    query = """
    insert in graph %s {
        ssu:%s a foaf:Person ;
        rdfs:label "%s" ; 
        foaf:firstName "%s" ;
        foaf:lastName "%s" ;
        foaf:mbox "%s" ;
        schema:accessCode "%s" ;
        sso:status "inactive" .
    }
    """ % (SSU, uid, uid, first_name, last_name, email, password)
    async with httpx.AsyncClient() as client:
        response = await core.send(client, query)

        if response == status.HTTP_200_OK:
            return Response(status_code=status.HTTP_200_OK, background=uid)

    return Response(status_code=status.HTTP_400_BAD_REQUEST)


async def exists(email: str):
    query = """ask from %s { ?s foaf:mbox "%s" }""" % (SSU, email)
    async with httpx.AsyncClient() as client:
        response = await core.send(client, query, format='bool')

        if response:
            return Response(status_code=status.HTTP_200_OK)

    return Response(status_code=status.HTTP_404_NOT_FOUND)


async def info():
    query = """
    with %s
    select ?id
    where {
        [] a foaf:Person ;
            rdfs:label ?id .
    }
    """ % SSU

    async with httpx.AsyncClient() as client:
        response = await core.send(client, query, format='var')

        if response:
            response = {'id': response}
            return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder(response))

    return Response(status_code=status.HTTP_404_NOT_FOUND)
