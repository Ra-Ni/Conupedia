from typing import Optional

import httpx
from fastapi import APIRouter, Request, Cookie, Response
from starlette import status
from starlette.responses import JSONResponse

from ..dependencies import core
from ..dependencies.models.course import Course
from ..dependencies.models.rating import Rating
from ..internals.globals import SSC

router = APIRouter()
categories = {}


@router.get('/courses/{id}')
async def get(id: str, token: Optional[str] = Cookie(None)):
    id = str(id).zfill(6)
    course = Course(uri='?c', id=id)
    course.fill_var(exclude=['description', 'requisite', 'similar'])

    query = """
            with %s
            select %s ?requisite ?description
            where {
                    %s 
                    optional {?c schema:coursePrerequisites ?requisite .}
                    optional {?c schema:description ?description .}
            }
            """ % (SSC, course.vars(), course.to_rdf())

    async with httpx.AsyncClient() as client:
        response = await core.send(client, query, format='dict')
        course.update(response)
        return JSONResponse(status_code=status.HTTP_200_OK, content=course.dict())


@router.get('/courses')
async def gets(request: Request, category: Optional[str] = None):
    func = categories[None if category not in categories else category]
    query = func(request)
    async with httpx.AsyncClient() as client:
        response = await core.send(client, query, format='records')
        if not response:
            return Response(status_code=status.HTTP_404_NOT_FOUND)

    return JSONResponse(status_code=status.HTTP_200_OK, content=response)


async def exists(id: str):
    course = Course(uri=id)
    query = """
    ask from %s { %s }
    """ % (SSC, course.to_rdf())

    async with httpx.AsyncClient() as client:
        response = await core.send(client, query, format='bool')
        if response:
            status_code = status.HTTP_200_OK
        else:
            status_code = status.HTTP_404_NOT_FOUND

    return Response(status_code=status_code)


def explore(request: Request, threshold: Optional[int] = 50):
    course = Course(id='?id')
    query = """
        select ?id
        where { %s } 
        order by rand()
        limit %s 
        """ % (course.to_rdf(), threshold)
    return query


def popular(request: Request, threshold: Optional[int] = 50):
    course = Course(uri='?c', id='?id')
    rating = Rating(value='like', subject='?c')
    query = """
    select ?id 
    where {
        %s
        {
            select ?c (count(?c) as ?count)
            where { %s } 
            group by ?c 
            order by desc(?count)
            limit %s
        }
    }
    """ % (course.to_rdf(), rating.to_rdf(), threshold)
    return query


def recommendations(request: Request, threshold: Optional[int] = 50):
    uid = request.state.user['id']
    first_rating = Rating(owner=uid, value='like', subject='?o').to_rdf()
    first = Course(uri='?o', similar='?c').to_rdf()
    second = Course(uri='?c', id='?id').to_rdf()
    second_rating = Rating(owner=uid, subject='?c').to_rdf()
    query = """
    select distinct ?id 
    where {
        %s
        %s
        %s
        filter not exists { 
            %s
        }
    } 
    group by ?id 
    order by rand()
    limit %s
    """ % (first_rating, first, second, second_rating, threshold)
    return query


def latest(request: Request, threshold: Optional[int] = 50):
    uid = request.state.user['id']
    course = Course(uri='?c', id='?id', dateCreated='?date')
    query = """
    select ?id
    where { %s } 
    order by rand() desc(?date) 
    limit %s 
    """ % (course.to_rdf(), threshold)
    return query


def likes(request: Request, threshold: Optional[int] = 50):
    uid = request.state.user['id']
    rating = Rating(owner=uid, value='like', subject='?c')
    course = Course(uri='?c', id='?id')
    query = """
    select distinct ?id
    where { %s %s }
    order by rand()
    limit %s
    """ % (rating.to_rdf(), course.to_rdf(), threshold)
    return query


def landing(request: Request, threshold: int = 50):
    course = Course(id='?id')
    query = """
    select *
    where { %s }
    order by rand()
    limit %s
    """ % (course.to_rdf(), threshold)
    return query


categories.update({
    None: landing,
    'likes': likes,
    'popular': popular,
    'recommendations': recommendations,
    'latest': latest,
    'explore': explore
})
