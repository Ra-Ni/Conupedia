import datetime
import http
from enum import Enum
from typing import Optional
import httpx
from fastapi import APIRouter, Request, Cookie, Response, Form, Depends
from fastapi.encoders import jsonable_encoder
from starlette import status
from starlette.responses import JSONResponse
from ..dependencies import core
from ..internals.globals import SSC

router = APIRouter()
categories = {}


def _gets(request: Request, threshold: int = 50):
    query = """
    select ?id
    where {
        [] a foaf:Person ;
            rdfs:label ?id .
    }
    order by rand()
    limit %s
    """ % threshold
    return query


categories[None] = _gets


@router.get('/courses')
async def gets(request: Request, category: Optional[str] = None):
    func = categories[None if category not in categories else category]
    query = func(request)
    async with httpx.AsyncClient() as client:
        response = await core.send(client, query, format='records')
        if not response:
            return Response(status_code=status.HTTP_404_NOT_FOUND)

    return JSONResponse(status_code=status.HTTP_200_OK, content=response)


@router.get('/courses/{id}')
async def get(id: str, token: Optional[str] = Cookie(None)):
    async with httpx.AsyncClient() as client:
        query = """
        with %s
        select ?id ?code ?title ?degree ?credit ?requisite ?description
        where {
            ?c a schema:Course ;
                rdfs:label ?id ;
                schema:courseCode ?code ;
                schema:name ?title ;
                schema:isPartOf ?degree ;
                schema:numberOfCredits ?credit .
                optional {?c schema:coursePrerequisites ?requisite .}
                optional {?c schema:description ?description .}
                filter("%s" = ?id)
        }
        """ % (SSC, str(id).zfill(6))

        response = await core.send(client, query, format='dict')
        return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder(response))


#
# @router.post('/course')
# async def admin(request: Request,
#                 response: Response,
#                 token: Optional[str] = Cookie(None),
#                 course_id: str = Form(...),
#                 code: str = Form(...),
#                 title: str = Form(...),
#                 credit: str = Form(...),
#                 degree: str = Form(...),
#                 requisites: Optional[str] = Form(None),
#                 description: Optional[str] = Form(None),
#                 ):
#     async with httpx.AsyncClient() as client:
#         current_time = datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
#         course_id = course_id.zfill(6)
#         requisites = requisites or ''
#         description = description or ''
#         query = """
#         modify %s
#         delete { ?s ?p ?o }
#         insert {
#             ?s rdfs:label "%s" ;
#             schema:courseCode "%s" ;
#             schema:coursePrerequisites "%s" ;
#             schema:description "%s" ;
#             schema:isPartOf "%s" ;
#             schema:name "%s" ;
#             schema:numberOfCredits "%s"^^xsd:float ;
#             schema:provider dbr:Concordia_University ;
#             schema:dateCreated "%s"^^xsd:dateTime .
#         }
#         where {
#             ?s rdfs:label "%s" ;
#                 ?p ?o .
#             filter ( ?p != rdfs:seeAlso )
#         }
#         """ % (SSC,
#                course_id,
#                code,
#                requisites,
#                description,
#                degree,
#                title,
#                credit,
#                current_time,
#                course_id
#                )
#
#         response = await core.send(client, query)
#
#     return response
#
#
# @router.delete('/course/{course_id}')
# async def course(course_id: str,
#                  request: Request,
#                  response: Response,
#                  token: Optional[str] = Cookie(None),
#                  ):
#     async with httpx.AsyncClient() as client:
#         course_id = course_id.zfill(6)
#         query = """
#         delete from %s { ?s ?p ?o . }
#         where {
#             ?s rdfs:label "%s" ;
#                 ?p ?o .
#         }
#         """ % (SSC, course_id)
#         response = await core.send(client, query)
#
#     return response
