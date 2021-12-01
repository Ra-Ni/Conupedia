from typing import Optional
import httpx
from fastapi import APIRouter, Request, Response
from starlette import status
from starlette.responses import JSONResponse
from ...dependencies import core


router = APIRouter()


@router.get('/explore')
async def get_explore(threshold: Optional[int] = 50):
    query = """
        select ?id
        where {
        ?c a schema:Course ;
            rdfs:label ?id .
        } 
        order by rand()
        limit %s 
        """ % (threshold)
    async with httpx.AsyncClient() as client:
        response = await core.send(client, query, format='records')
        if not response:
            return Response(status_code=status.HTTP_404_NOT_FOUND)

        return JSONResponse(status_code=status.HTTP_200_OK, content=response)


@router.get('/popular')
async def popular(threshold: Optional[int] = 50):
    query = """
    select ?id 
    where {
        ?c a schema:Course ;
            rdfs:label ?id 
        {
            select ?c (count(?c) as ?count)
            where { [] sso:likes ?c .} 
            group by ?c 
            order by desc(?count)
            limit %s
        }
    }
    """ % threshold
    async with httpx.AsyncClient() as client:
        response = await core.send(client, query, format='records')
    if not response:
        return Response(status_code=status.HTTP_404_NOT_FOUND)

    return JSONResponse(status_code=status.HTTP_200_OK, content=response)


@router.get('/recommendations')
async def recommendations(request: Request, threshold: Optional[int] = 50):
    uid = request.state.user['id']
    query = """
    select distinct ?id 
    where {
        ssu:%s sso:likes ?o .
        ?o rdfs:seeAlso ?c .
        ?c  rdfs:label ?id 
        filter not exists { ssu:%s [] ?c }
    } 
    group by ?id 
    order by rand()
    limit %s
    """ % (uid, uid, threshold)

    async with httpx.AsyncClient() as client:
        response = await core.send(client, query, format='records')
    if not response:
        return Response(status_code=status.HTTP_404_NOT_FOUND)

    return JSONResponse(status_code=status.HTTP_200_OK, content=response)


@router.get('/latest')
async def latest(request: Request, threshold: Optional[int] = 50):
    uid = request.state.user['id']
    query = """
    select ?id
    where {
    ?c a schema:Course ;
        rdfs:label ?id ;
        schema:dateCreated ?date .
    filter not exists { ssu:%s ?p ?c }
    } 
    order by rand() desc(?date) 
    limit %s 
    """ % (uid, threshold)
    async with httpx.AsyncClient() as client:
        response = await core.send(client, query, format='records')
        if not response:
            return Response(status_code=status.HTTP_404_NOT_FOUND)

        return JSONResponse(status_code=status.HTTP_200_OK, content=response)


@router.get('/likes')
async def latest(request: Request, threshold: Optional[int] = 50):
    uid = request.state.user['id']
    query = """
    select distinct ?id
    where {
        ssu:%s sso:likes ?c .
        ?c  rdfs:label ?id .
    }
    order by rand()
    limit %s
    """ % (uid, threshold)
    async with httpx.AsyncClient() as client:
        response = await core.send(client, query, format='records')
        if not response:
            return Response(status_code=status.HTTP_404_NOT_FOUND)

        return JSONResponse(status_code=status.HTTP_200_OK, content=response)
