import uuid

import shortuuid

from app.internals.namespaces import sst, ssu
from .base import build


def delete(token: str):
    query = """
    delete { ?s ?p ?o }
    where { 
        graph %s {
            ?s a sso:Token ;
                rdf:value "%s" ;
                ?p ?o .
        }
    } 
    """ % (sst, token)

    return build(query)


def to_user(token: str):
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
    """ % (sst, token, ssu)

    return build(query)


def new(user: str):
    tid = shortuuid.uuid()
    token = uuid.uuid4().hex + uuid.uuid4().hex
    query = """
    insert in graph %s {
        sst:%s a sso:Token ;
            rdfs:label "%s" ;
            rdf:value "%s" ;
            rdfs:seeAlso %s .
    } 
    """ % (sst, tid, tid, token, user)

    return build(query), token
