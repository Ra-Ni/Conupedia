import uuid

import httpx
import shortuuid
from ..internals import namespaces
from . import core


class InvalidCredentials(Exception):
    pass


async def create(client: httpx.AsyncClient, user_id: str) -> str:
    token_id = shortuuid.uuid()
    token = uuid.uuid4().hex + uuid.uuid4().hex
    query = """
    insert in graph %s {
        sst:%s a sso:Token ;
            rdfs:label "%s" ;
            rdf:value "%s" ;
            rdfs:seeAlso %s .
    } 
    """ % (namespaces.sst, token_id, token_id, token, user_id)
    await core.send(client, query)
    return token


async def delete(client: httpx.AsyncClient, token: str) -> None:
    query = """
    delete { ?s ?p ?o }
    where { 
        graph %s {
            ?s a sso:Token ;
                rdf:value "%s" ;
                ?p ?o .
        }
    } 
    """ % (namespaces.sst, token)
    await core.send(client, query)


async def verify(client: httpx.AsyncClient, token: str, as_root: bool = False) -> None:
    if not token:
        raise InvalidCredentials('Token supplied not in database: "%s"' % token)

    suffix = ''
    if as_root:
        suffix = """
        graph %s {
            ?id sso:isAdmin "true"^^xsd:boolean .
        }
        """ % namespaces.ssu

    query = """
    ask { 
        graph %s {
            [] a sso:Token ; 
                rdf:value "%s" ;
                rdfs:seeAlso ?id .
        }
        %s
    }
    """ % (namespaces.sst, token, suffix)
    response = await core.send(client, query, format='bool')

    if not response:
        raise InvalidCredentials('Token supplied not in database: "%s"' % token)


async def get_user(client: httpx.AsyncClient, token: str) -> dict:
    if not token:
        raise InvalidCredentials('Token supplied not in database: "%s"' % token)

    query = """
    select ?id ?firstName ?lastName ?mbox ?password
    where { 
        graph %s {
            ?s a sso:Token ;
                rdf:value "%s" ;
                rdfs:seeAlso ?id .
        }
        graph %s {
            ?id foaf:firstName ?firstName ;
                foaf:lastName ?lastName ;
                foaf:mbox ?mbox ;
                schema:accessCode ?password .
        }

    } 
    """ % (namespaces.sst, token, namespaces.ssu)
    response = await core.send(client, query, format='dict')

    if not response:
        raise InvalidCredentials('Token supplied not in database: "%s"' % token)

    return response
