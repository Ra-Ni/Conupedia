import uuid
from typing import Optional

import httpx
import shortuuid
from fastapi import Response, Cookie
from fastapi.encoders import jsonable_encoder
from jose import jwt, JWTError, ExpiredSignatureError
from jose.exceptions import JWTClaimsError
from passlib.context import CryptContext
from starlette import status
from starlette.responses import RedirectResponse

from . import core
from ..internals.globals import SST, SSU, ENCRYPTION_SECRET_KEY, ENCRYPTION_ALGORITHM, TOKEN_KEEP_ALIVE
from datetime import datetime, timedelta


class InvalidCredentials(Exception):
    pass


async def post(data: dict):
    expire = datetime.utcnow() + timedelta(minutes=TOKEN_KEEP_ALIVE)
    to_encode = data.copy()
    data['exp'] = expire
    encoded_jwt = jwt.encode(to_encode, ENCRYPTION_SECRET_KEY, algorithm=ENCRYPTION_ALGORITHM)

    response = Response(status_code=status.HTTP_201_CREATED)
    response.set_cookie('token', encoded_jwt)
    response.background = encoded_jwt
    return response


async def delete(response: Response):
    response.delete_cookie('token')
    return response


async def get(token: Optional[str] = Cookie(None)) -> Response:
    if not token:
        return Response(status_code=status.HTTP_403_FORBIDDEN)


    try:
        payload = jwt.decode(token, ENCRYPTION_SECRET_KEY, algorithms=[ENCRYPTION_ALGORITHM])
    except (JWTError, ExpiredSignatureError, JWTClaimsError) as _:
        return Response(status_code=status.HTTP_403_FORBIDDEN)

    uid: str = payload.get('id')
    email: str = payload.get('email')
    password: str = payload.get('password')

    query = """
    ask from %s {
        ssu:%s a foaf:Person ;
            foaf:mbox "%s" ;
            schema:accessCode "%s" .
    }
    """ % (SSU, uid, email, password)

    async with httpx.AsyncClient() as client:
        response = await core.send(client, query, format='bool')

    if not response:
        return Response(status_code=status.HTTP_403_FORBIDDEN)

    return Response(status_code=status.HTTP_200_OK, background=payload)

