import datetime
from typing import Optional
import httpx
import shortuuid
from fastapi import APIRouter, Request, Cookie, Response, Form
from fastapi.encoders import jsonable_encoder
from starlette import status
from starlette.responses import JSONResponse

from ..dependencies import auth, core
from ..internals.globals import SSC, SSU


async def get_user(id: str):
    query = """
    with %s
    select ?id ?firstName ?lastName ?email ?password ?status
    where { 
        ?id a foaf:Person ;
            foaf:firstName ?firstName ;
            foaf:lastName ?lastName ;
            foaf:mbox ?email ;
            schema:accessCode ?password ;
            sso:status ?status 
        filter (?id = "%s")
    } 
    """ % (SSU, id)
    async with httpx.AsyncClient() as client:
        response = await core.send(client, query, 'dict')

    if not response:
        return Response(status_code=status.HTTP_404_NOT_FOUND)

    return Response(status_code=status.HTTP_200_OK, content=jsonable_encoder(response))


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
