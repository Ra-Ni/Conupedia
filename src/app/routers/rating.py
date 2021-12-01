import re
from typing import Optional
import httpx
from fastapi import APIRouter, Cookie, Form, Request
from ..dependencies import core
from ..internals.globals import SSU, SSC

router = APIRouter()


@router.get('/rating')
async def rating(id: str, request: Request, token: Optional[str] = Cookie(None)):
    async with httpx.AsyncClient() as client:
        course_id = f'ssc:{id.zfill(6)}'
        await _verify_course(client, course_id)
        uid = f'ssu:{request.state.user["id"]}'
        reaction = await _get_rating(client, uid, course_id)

        if not reaction:
            return reaction
        reaction = re.sub(r'.*:(.*).', r'\1', reaction)
        return reaction


@router.post('/rating')
async def rating(request: Request, cid: str = Form(...), value: str = Form(...), token: Optional[str] = Cookie(None)):
    async with httpx.AsyncClient() as client:
        course_id = f'ssc:{cid.zfill(6)}'
        await _verify_course(client, course_id)
        user_id = f'ssu:{request.state.user["id"]}'
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
        """ % (SSU, delete, insert)
        await core.send(client, query)


class InvalidCourse(Exception):
    pass


async def _verify_course(client: httpx.AsyncClient, course_id: str):
    query = """
    ask from %s { %s a schema:Course }
    """ % (SSC, course_id)
    response = await core.send(client, query, format='bool')
    if not response:
        raise InvalidCourse("Course %s does not exist." % course_id)


async def _get_rating(client: httpx.AsyncClient, user_id: str, course_id: str) -> str:
    query = """
        select ?reaction where {
            graph %s {
                values ?reaction { sso:likes sso:dislikes }
                %s ?reaction %s .
            }
    }
    """ % (SSU, user_id, course_id)
    response = await core.send(client, query, format='var')
    return response
