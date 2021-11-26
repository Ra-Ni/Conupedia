import re
from typing import Optional
import httpx
from fastapi import APIRouter, Cookie, Form
from ..dependencies import auth, core
from ..internals import namespaces

router = APIRouter()


@router.get('/rating')
async def rating(id: str, token: Optional[str] = Cookie(None)):
    async with httpx.AsyncClient() as client:
        user = await auth.get_user(client, token)
        user_id = user['id']
        course_id = f'ssc:{id.zfill(6)}'
        reaction = await _get_rating(client, user_id, course_id)

        if not reaction:
            return reaction
        reaction = re.sub(r'.*:(.*).', r'\1', reaction)
        return reaction


@router.post('/rating')
async def rating(cid: str = Form(...), value: str = Form(...), token: Optional[str] = Cookie(None)):
    async with httpx.AsyncClient() as client:
        user = await auth.get_user(client, token)

        user_id = user['id']
        course_id = f'ssc:{cid.zfill(6)}'

        reaction = f'sso:{value}s'
        db_reaction = await _get_rating(client, user_id, course_id)

        if db_reaction == reaction:
            insert = ''
        else:
            insert = f'{user_id} {reaction} {course_id}'

        if db_reaction:
            delete = f'{user_id} {db_reaction} {course_id}'
        else:
            delete = ''

        query = """
        modify %s
        delete {%s}
        insert {%s}
        """ % (namespaces.ssu, delete, insert)
        await core.send(client, query)


async def _get_rating(client: httpx.AsyncClient, user_id: str, course_id: str) -> str:
    query = """
        select ?reaction  {
            graph %s {
                values ?reaction { sso:likes sso:dislikes }
                %s ?reaction %s .
            }
    }
    """ % (namespaces.ssu, user_id, course_id)
    response = await core.send(client, query, format='var')
    return response
