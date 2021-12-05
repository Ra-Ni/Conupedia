import json
from typing import Optional
import httpx
from fastapi import APIRouter, Request, Response
from starlette import status
from starlette.responses import JSONResponse, RedirectResponse

from .. import user
from ...dependencies import core
from ...internals.globals import SSU

router = APIRouter()


@router.get('/activate')
async def get(id: str):
    response = await user.get_user(id)
    if response.status_code != status.HTTP_200_OK:
        return response

    profile = json.loads(response.body)
    status_ = profile['status']
    if status_ != 'inactive':
        return Response(status_code=status.HTTP_403_FORBIDDEN)

    query = """
    modify %s
    delete { ssu:%s sso:status "inactive" }
    insert { ssu:%s sso:status "member" }
    """ % (SSU, id, id)

    async with httpx.AsyncClient() as client:
        await core.send(client, query)

    return RedirectResponse(url='/login', status_code=status.HTTP_302_FOUND)
