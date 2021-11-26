import re
from typing import Optional
import httpx
import pandas as pd
from fastapi import APIRouter, Request, Response, Cookie, Form
from starlette import status
from starlette.responses import RedirectResponse
from ..internals.globals import TEMPLATES, SPARQL
from ..virtuoso import users, base, auth, recommendations
from ..internals import namespaces

router = APIRouter()


@router.get('/rating')
async def rating(id: str, sessionID: Optional[str] = Cookie(None)):
    if not sessionID:
        return RedirectResponse(url='/login')

    id = f'ssc:{id.zfill(6)}'
    query = users.get_reaction(sessionID, id)

    async with httpx.AsyncClient() as client:

        reaction = await client.get(SPARQL, params=query)
        reaction = base.to_frame(reaction)

        if reaction.empty or pd.isna(reaction.iat[0, 1]):
            return ''

        reaction = re.sub(r'.*:(.*).', r'\1', reaction.iat[0, 1])
        return reaction


@router.post('/rating')
async def rating(cid: str = Form(...),
                 value: str = Form(...),
                 sessionID: Optional[str] = Cookie(None)):
    if not sessionID:
        return RedirectResponse(url='/login', status_code=status.HTTP_302_FOUND)

    value = f'sso:{value}s'
    course = f'ssc:{cid.zfill(6)}'
    query = users.get_reaction(sessionID, course)

    async with httpx.AsyncClient() as client:
        response = await client.get(SPARQL, params=query)
        response = base.to_frame(response)

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
        """ % (namespaces.ssu, delete, insert)
        query = base.build(query)
        response = await client.get(SPARQL, params=query)
