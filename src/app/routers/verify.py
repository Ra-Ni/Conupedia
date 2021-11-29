import httpx
from fastapi import APIRouter
from starlette import status
from starlette.responses import RedirectResponse
from ..dependencies import core
from ..internals.globals import SSU

router = APIRouter()


class ActivationError(Exception):
    pass


@router.get('/verify')
async def verify(id: str):
    async with httpx.AsyncClient() as client:
        query = """
        ask from %s {
            ?user sso:hasVerification "%s" 
        }
        """ % (SSU, id)

        response = await core.send(client, query, format='bool')

        if not response:
            raise ActivationError('The user has already been verified')

        query = """
        modify %s
        delete { 
            ?u sso:hasVerification ?v ;
                sso:status "inactive" .
        }
        insert { ?u sso:status "active" }
        where { 
            bind("%s" as ?v)
            ?u sso:hasVerification ?v 
        } 
        """ % (SSU, id)

        await core.send(client, query)

        return RedirectResponse(url='/login', status_code=status.HTTP_302_FOUND)

