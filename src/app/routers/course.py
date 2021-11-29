import datetime
from typing import Optional
import httpx
from fastapi import APIRouter, Request, Cookie, Response, Form
from ..dependencies import auth, core
from ..internals.globals import SSC


router = APIRouter()


@router.get('/course')
async def course(id: str, token: Optional[str] = Cookie(None)):
    async with httpx.AsyncClient() as client:
        await auth.verify(client, token)

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
        """ % (SSC, str(id).zfill(6))

        response = await core.send(client, query, format='dict')

        return response


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
        await auth.verify(client, token, as_root=True)

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
        await auth.verify(client, token, as_root=True)
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
