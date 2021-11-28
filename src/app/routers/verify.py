from http.client import HTTPException
from typing import Optional
import httpx
import shortuuid
from fastapi import APIRouter, Request, Cookie, Form
from starlette import status
from starlette.responses import RedirectResponse
from ..internals.globals import TEMPLATES
from ..dependencies import core
from ..internals import namespaces


router = APIRouter()


@router.get('/verify')
async def verify(id: str):
    async with httpx.AsyncClient() as client:
        query = """
        ask from %s {
            ?user sso:hasVerification "%s" 
        }
        """ % (namespaces.ssu, id)

        response = await core.send(client, query, format='bool')

        if not response:
            raise HTTPException("Verification not found.")

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
        """ % (namespaces.ssu, id)

        await core.send(client, query)

        return RedirectResponse(url='/login', status_code=status.HTTP_302_FOUND)

