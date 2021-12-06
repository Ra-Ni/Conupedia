from typing import Optional
import httpx
from fastapi import APIRouter, Request, Response
from starlette import status
from starlette.responses import JSONResponse

from .. import course
from ...dependencies import core

router = APIRouter()


def explore(request: Request, threshold: Optional[int] = 50):
    query = """
        select ?id
        where {
        ?c a schema:Course ;
            rdfs:label ?id .
        } 
        order by rand()
        limit %s 
        """ % threshold
    return query


def popular(request: Request, threshold: Optional[int] = 50):
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
    return query


def recommendations(request: Request, threshold: Optional[int] = 50):
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
    return query


def latest(request: Request, threshold: Optional[int] = 50):
    uid = request.state.user['id']
    query = """
    select ?id
    where {
    ?c a schema:Course ;
        rdfs:label ?id ;
        schema:dateCreated ?date .
    filter not exists { ssu:%s ?p ?c }
    } 
    order by rand() desc(?date) 
    limit %s 
    """ % (uid, threshold)
    return query


def likes(request: Request, threshold: Optional[int] = 50):
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
    return query


course.categories.update({
    'likes': likes,
    'popular': popular,
    'recommendations': recommendations,
    'latest': latest,
    'explore': explore
})
