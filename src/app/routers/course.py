import asyncio
from typing import Optional
import httpx
from fastapi import APIRouter, Request, Cookie, Response
from ..internals.globals import TEMPLATES
from ..internals import namespaces
from ..dependencies import auth, core

router = APIRouter()


@router.get('/course')
async def course(id: str, token: Optional[str] = Cookie(None)):
    async with httpx.AsyncClient() as client:
        await auth.verify(client, token, as_root=True)

        query = """
        with %s
        select ?code ?title ?degree ?credits ?requisites ?description
        where {
            ?id a schema:Course ;
                rdfs:label "%s" ;
                schema:courseCode ?code ;
                schema:name ?title ;
                schema:isPartOf ?degree ;
                schema:numberOfCredits ?credits .
                optional {
                    ?id schema:coursePrerequisites ?requisites .
                }
                optional {
                    ?id schema:description ?description .
                }
        }
        """ % (namespaces.ssc, str(id).zfill(6))

        response = await core.send(client, query, format='dict')
        return response

