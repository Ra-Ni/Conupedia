from typing import Optional

import httpx
import shortuuid
from fastapi import Response
from starlette import status
from starlette.responses import JSONResponse

from ..dependencies import core
from ..dependencies.models.user import User
from ..internals.globals import SSU


async def get(id: str):
    user = User(id=id)
    query = """
    with %s
    select *
    where { %s } 
    """ % (SSU, user.to_rdf())

    async with httpx.AsyncClient() as client:
        response = await core.send(client, query, 'dict')
        if response:
            user.update(response)
            return JSONResponse(status_code=status.HTTP_200_OK, content=user.dict())

    return Response(status_code=status.HTTP_404_NOT_FOUND)


async def gets(id: Optional[str] = None,
               first_name: Optional[str] = None,
               last_name: Optional[str] = None,
               email: Optional[str] = None,
               password: Optional[str] = None,
               status_: Optional[str] = None):
    user = User(id=id,
                first_name=first_name,
                last_name=last_name,
                email=email,
                password=password,
                status=status_)
    user.fill_var(exclude=['dislikes', 'likes'])

    query = """
    with %s
    select *
    where { %s }
    """ % (SSU, user.to_rdf())

    async with httpx.AsyncClient() as client:
        response = await core.send(client, query, format='dict')
        if response:
            user.update(response)
            return JSONResponse(status_code=status.HTTP_200_OK, content=user.dict())

    return Response(status_code=status.HTTP_404_NOT_FOUND)


async def post(email: str, password: str, first_name: str, last_name: str):
    uid = shortuuid.uuid()
    user = User(email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                status='inactive',
                id=uid,
                uri=uid)

    query = """
    insert in graph %s { %s }
    """ % (SSU, user.to_rdf())

    async with httpx.AsyncClient() as client:
        response = await core.send(client, query)

        if response == status.HTTP_200_OK:
            return Response(status_code=status.HTTP_200_OK, background=uid)

    return Response(status_code=status.HTTP_400_BAD_REQUEST)


async def patch(id: str,
                first_name: Optional[str] = None,
                last_name: Optional[str] = None,
                email: Optional[str] = None,
                password: Optional[str] = None,
                status_: Optional[str] = None):
    insert = User(uri=id,
                  first_name=first_name,
                  last_name=last_name,
                  email=email,
                  password=password,
                  status=status_)
    delete = insert.to_query(exclude=['uri', 'type'])

    insert = insert.to_rdf(exclude=['type'])
    delete = delete.to_rdf(exclude=['type'])

    query = """
    modify %s
    delete { %s }
    insert { %s }
    where { %s }
    """ % (SSU, delete, insert, delete)
    print(query)
    async with httpx.AsyncClient() as client:
        response = await core.send(client, query)

        if response == status.HTTP_200_OK:
            return Response(status_code=status.HTTP_200_OK)

    return Response(status_code=status.HTTP_400_BAD_REQUEST)


async def exists(uri: Optional[str] = None,
                 id: Optional[str] = None,
                 first_name: Optional[str] = None,
                 last_name: Optional[str] = None,
                 email: Optional[str] = None,
                 password: Optional[str] = None,
                 status_: Optional[str] = None):
    user = User(uri=uri,
                id=id,
                first_name=first_name,
                last_name=last_name,
                email=email,
                password=password,
                status=status_)
    user = user.to_rdf()
    query = """ask from %s { %s }""" % (SSU, user)

    async with httpx.AsyncClient() as client:
        response = await core.send(client, query, format='bool')

        if response:
            return Response(status_code=status.HTTP_200_OK)

    return Response(status_code=status.HTTP_404_NOT_FOUND)
