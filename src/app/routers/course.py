import datetime
from typing import Optional
import httpx
from fastapi import APIRouter, Request, Cookie, Response, Form
from fastapi.encoders import jsonable_encoder
from starlette import status
from starlette.responses import JSONResponse

from . import user
from ..dependencies import auth, core
from ..internals.globals import SSC

router = APIRouter()


@router.get('/explore')
async def get_explore(threshold: Optional[int] = 50):
    query = """
        select ?id
        where {
        [] a schema:Course ;
            rdfs:label ?id .
        } 
        order by rand()
        limit %s 
        """ % (threshold)
    async with httpx.AsyncClient() as client:
        response = await core.send(client, query, format='records')
        if not response:
            return Response(status_code=status.HTTP_404_NOT_FOUND)

        return JSONResponse(status_code=status.HTTP_200_OK, content=response)


@router.get('/popular')
async def popular(threshold: Optional[int] = 50):
    query = """
    select ?id 
    where {
        ?c a schema:Course ;
            rdfs:label ?id 
        {
            select ?c (count(?c) as ?count)
            where { [] sso:likes ?c .} 
            group by ?c 
            order by desc(?count)
            limit %s
        }
    }
    """ % threshold
    async with httpx.AsyncClient() as client:
        response = await core.send(client, query, format='records')
    if not response:
        return Response(status_code=status.HTTP_404_NOT_FOUND)

    return JSONResponse(status_code=status.HTTP_200_OK, content=response)


@router.get('/recommendations')
async def recommendations(request: Request, threshold: Optional[int] = 50):
    uid = request.state.user['id']
    query = """
    select distinct ?id 
    where {
        ssu:%s sso:likes ?o .
        ?o rdfs:seeAlso ?c .
        ?c  rdfs:label ?id 
        filter not exists { ssu:%s [] ?c }
    } 
    group by ?id 
    order by rand()
    limit %s
    """ % (uid, uid, threshold)

    async with httpx.AsyncClient() as client:
        response = await core.send(client, query, format='records')
    if not response:
        return Response(status_code=status.HTTP_404_NOT_FOUND)

    return JSONResponse(status_code=status.HTTP_200_OK, content=response)


@router.get('/latest')
async def latest(request: Request, threshold: Optional[int] = 50):
    uid = request.state.user['id']
    query = """
    select ?id
    where {
    ?c a schema:Course ;
        rdfs:label ?id ;
        schema:dateCreated ?date .
    filter not exists { ssu:%s [] ?c }
    } 
    order by rand() desc(?date) 
    limit %s 
    """ % (uid, threshold)
    async with httpx.AsyncClient() as client:
        response = await core.send(client, query, format='records')
        if not response:
            return Response(status_code=status.HTTP_404_NOT_FOUND)

        return JSONResponse(status_code=status.HTTP_200_OK, content=response)


@router.get('/likes')
async def latest(request: Request, threshold: Optional[int] = 50):
    uid = request.state.user['id']
    query = """
    select distinct ?id
    where {
        ssu:%s sso:likes ?c .
        ?c  rdfs:label ?id .
    }
    order by rand()
    limit %s
    """ % (uid, threshold)
    async with httpx.AsyncClient() as client:
        response = await core.send(client, query, format='records')
        if not response:
            return Response(status_code=status.HTTP_404_NOT_FOUND)

        return JSONResponse(status_code=status.HTTP_200_OK, content=response)


@router.get('/course')
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


@router.post('/course')
async def admin(request: Request,
                response: Response,
                token: Optional[str] = Cookie(None),
                course_id: str = Form(...),
                code: str = Form(...),
                title: str = Form(...),
                credit: str = Form(...),
                degree: str = Form(...),
                requisites: Optional[str] = Form(None),
                description: Optional[str] = Form(None),
                ):
    async with httpx.AsyncClient() as client:
        current_time = datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
        course_id = course_id.zfill(6)
        requisites = requisites or ''
        description = description or ''
        query = """
        modify %s
        delete { ?s ?p ?o }
        insert { 
            ?s rdfs:label "%s" ;
            schema:courseCode "%s" ;
            schema:coursePrerequisites "%s" ;
            schema:description "%s" ;
            schema:isPartOf "%s" ;
            schema:name "%s" ;
            schema:numberOfCredits "%s"^^xsd:float ;
            schema:provider dbr:Concordia_University ;
            schema:dateCreated "%s"^^xsd:dateTime .
        }
        where {
            ?s rdfs:label "%s" ;
                ?p ?o .
            filter ( ?p != rdfs:seeAlso )
        }
        """ % (SSC,
               course_id,
               code,
               requisites,
               description,
               degree,
               title,
               credit,
               current_time,
               course_id
               )

        response = await core.send(client, query)

    return response


@router.delete('/course/{course_id}')
async def course(course_id: str,
                 request: Request,
                 response: Response,
                 token: Optional[str] = Cookie(None),
                 ):
    async with httpx.AsyncClient() as client:
        course_id = course_id.zfill(6)
        query = """
        delete from %s { ?s ?p ?o . }
        where { 
            ?s rdfs:label "%s" ; 
                ?p ?o . 
        }
        """ % (SSC, course_id)
        response = await core.send(client, query)

    return response
