import json
from typing import Optional

import httpx
import shortuuid
from fastapi import APIRouter, Form, Request
from starlette import status
from starlette.responses import JSONResponse, Response

from . import course
from ..dependencies import core
from ..dependencies.models.rating import Rating
from ..internals.globals import SSR

router = APIRouter()


async def get(id: str):
    rating = Rating(uri=id)
    rating.fill_var()
    rating = rating.to_rdf()
    query = """
    with %s
    select *
    where { %s }
    """ % (SSR, rating)

    async with httpx.AsyncClient() as client:
        response = await core.send(client, query, format='dict')
        return JSONResponse(content=response)


@router.post('/ratings')
async def post(request: Request, cid: str = Form(...), value: str = Form(...)):
    cid = cid.zfill(6)
    uid = request.state.user["id"]
    r = Rating(owner=uid, subject=cid, value=value)

    response = await course.exists(cid)
    if response.status_code != status.HTTP_200_OK:
        return Response(status_code=status.HTTP_400_BAD_REQUEST)

    response = await gets(request, cid=cid)
    response = json.loads(response.body)
    if 'id' in response:
        id = response['id']

        if response['value'] != value:
            return await patch(id=id, value=value)
        else:
            return await delete_(id=id)

    id = shortuuid.uuid()
    rating = Rating(uri=id, id=id, value=value, owner=uid, subject=cid).to_rdf()
    query = """
    insert in %s { %s }
    """ % (SSR, rating)
    async with httpx.AsyncClient() as client:
        await core.send(client, query)


@router.get('/ratings')
async def gets(request: Request,
               id: Optional[str] = None,
               cid: Optional[str] = None,
               value: Optional[str] = None):
    uid = request.state.user['id']
    rating = Rating(id=id, owner=uid, subject=cid, value=value)
    rating.fill_var()
    rating = rating.to_rdf()
    query = """
    with %s
    select * 
    where { %s }
    """ % (SSR, rating)
    async with httpx.AsyncClient() as client:
        response = await core.send(client, query, format='records')
        if len(response) == 1:
            response = response[0]

        return JSONResponse(content=response)


async def patch(id: str, value: str):
    insert = Rating(uri=id, value=value).to_rdf()
    delete = Rating(uri=id, value='?value').to_rdf()
    query = """
    modify %s
    delete { %s }
    insert { %s }
    where { %s }
    """ % (SSR, delete, insert, delete)

    async with httpx.AsyncClient() as client:
        await core.send(client, query)


async def delete_(id: str):
    rating = Rating(uri=id, id=id)
    rating.fill_var()
    rating = rating.to_rdf()
    query = """
    delete from %s { %s }
    where { %s }
    """ % (SSR, rating, rating)
    async with httpx.AsyncClient() as client:
        await core.send(client, query)


async def exists(id: Optional[str] = None,
                 uid: Optional[str] = None,
                 cid: Optional[str] = None,
                 value: Optional[str] = None):
    rating = Rating(id=id, owner=uid, subject=cid, value=value)
    rating.fill_var()
    query = """
        ask from %s { %s }
        """ % (SSR, rating.to_rdf())
    async with httpx.AsyncClient() as client:
        response = await core.send(client, query, format='bool')

        if not response:
            status_code = status.HTTP_404_NOT_FOUND
        else:
            status_code = status.HTTP_200_OK

    return Response(status_code=status_code)
