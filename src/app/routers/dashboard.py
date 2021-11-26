import asyncio
from typing import Optional
import httpx
from fastapi import APIRouter, Request, Cookie
from ..internals.globals import TEMPLATES
from ..dependencies import auth, core

router = APIRouter()


@router.get('/dashboard')
async def dashboard(request: Request, token: Optional[str] = Cookie(None)):
    async with httpx.AsyncClient() as client:
        user = await auth.get_user(client, token)
        user_id = user['id']

        results = await asyncio.gather(
            get_recommendation(client, user_id),
            get_popular(client),
            get_explore(client, user_id),
            get_latest(client, user_id),
            get_likes(client, user_id)
        )

        categories = dict(results)
        context = {'request': request, 'user_info': user,'categories': categories}

        return TEMPLATES.TemplateResponse('dashboard.html', context=context)


async def get_popular(client: httpx.AsyncClient, threshold: int = 50):
    query = """
    select ?course ?code ?title ?credits ?partOf ?description 
    where {
        ?c a schema:Course ;
            rdfs:label ?course ;
            schema:courseCode ?code ;
            schema:name ?title ;
            schema:numberOfCredits ?credits ;
            schema:isPartOf ?partOf ;
            schema:description ?description .
        {
            select ?c (count(?c) as ?count)
            where { [] sso:likes ?c .} 
            group by ?c 
            order by desc(?count)
            limit %s
        }
    }
    """ % threshold
    response = await core.send(client, query, format='records')
    return 'Popular', response


async def get_latest(client: httpx.AsyncClient, user: str, threshold: int = 50):
    query = """
    select *
    where {
    ?c a schema:Course ;
        rdfs:label ?course ;
        schema:courseCode ?code ;
        schema:name ?title ;
        schema:numberOfCredits ?credits ;
        schema:isPartOf ?partOf ;
        schema:description ?description ;
        schema:dateCreated ?date .
    filter not exists { %s [] ?c }
    } 
    order by desc(?date) 
    limit %s 
    """ % (user, threshold)
    response = await core.send(client, query, format='records')
    return 'Latest', response


async def get_explore(client: httpx.AsyncClient, user: str, threshold: int = 50):
    query = """
    select ?course ?code ?title ?credits ?partOf ?description
    where {
    ?c a schema:Course ;
        rdfs:label ?course ;
        schema:courseCode ?code ;
        schema:name ?title ;
        schema:numberOfCredits ?credits ;
        schema:isPartOf ?partOf ;
        schema:description ?description .
        filter not exists { %s [] ?c }
    } 
    order by rand()
    limit %s 
    """ % (user, threshold)
    response = await core.send(client, query, format='records')
    return 'Explore', response


async def get_recommendation(client: httpx.AsyncClient, user: str, threshold: int = 50):
    query = """
    select distinct ?course ?code ?title ?credits ?partOf ?description 
    where {
        %s sso:likes ?o .
        ?o rdfs:seeAlso ?c .
        ?c  rdfs:label ?course ;
            schema:courseCode ?code ;
            schema:name ?title ;
            schema:numberOfCredits ?credits ;
            schema:isPartOf ?partOf ;
            schema:description ?description .
        filter not exists { %s [] ?c }
    } 
    group by ?course 
    order by rand()
    limit %s
    """ % (user, user, threshold)
    response = await core.send(client, query, format='records')
    return 'Recommendations', response


async def get_likes(client: httpx.AsyncClient, user: str, threshold: int = 50):
    query = """
    select distinct ?course ?code ?title ?credits ?partOf ?description
    where {
        %s sso:likes ?c .
        ?c  rdfs:label ?course ;
            schema:courseCode ?code ;
            schema:name ?title ;
            schema:numberOfCredits ?credits ;
            schema:isPartOf ?partOf ;
            schema:description ?description .
    }
    """ % user
    response = await core.send(client, query, format='records')
    return 'Likes', response

