import uuid
import httpx
import shortuuid
from . import core
from ..internals.globals import SST, SSU


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
    """ % (SST, token_id, token_id, token, user_id)
    await core.send(client, query)
    return token


async def delete(client: httpx.AsyncClient, token: str) -> None:
    query = """
    delete from %s { ?s ?p ?o }
    where { 
        ?s a sso:Token ;
            rdf:value "%s" ;
            ?p ?o .
    } 
    """ % (SST, token)
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
        """ % SSU

    query = """
    ask { 
        graph %s {
            [] a sso:Token ; 
                rdf:value "%s" ;
                rdfs:seeAlso ?id .
        }
        %s
    }
    """ % (SST, token, suffix)
    response = await core.send(client, query, format='bool')

    if not response:
        raise InvalidCredentials('Token supplied not in database: "%s"' % token)


async def get_user(client: httpx.AsyncClient, token: str, as_root: bool = False) -> dict:
    if not token:
        raise InvalidCredentials('Token supplied not in database: "%s"' % token)

    suffix = ''
    if as_root:
        suffix = '?id sso:isAdmin "true"^^xsd:boolean .'

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
                %s
        }

    } 
    """ % (SST, token, SSU, suffix)
    response = await core.send(client, query, format='dict')

    if not response:
        raise InvalidCredentials('Token supplied not in database: "%s"' % token)

    return response
