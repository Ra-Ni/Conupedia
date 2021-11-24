import shortuuid

from virtuoso.namespace import ssu, sst
from virtuoso.base import build, hash_password


def exists_email(email: str):
    query = """
    ask from %s { ?s foaf:mbox "%s" }
    """ % (ssu, email)
    build(query)


def from_token(token: str):
    query = """
        select ?id ?firstName ?lastName ?mbox ?password
        where { 
            graph %s {
                [] a sso:Token ;
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


def from_email(email: str):
    query = """
        select ?id ?firstName ?lastName ?password
        where { 
            graph %s {
                ?id foaf:firstName ?firstName ;
                    foaf:lastName ?lastName ;
                    foaf:mbox "%s" ;
                    schema:accessCode ?password .
            }

        } 
        """ % (ssu, email)

    return build(query)


def new(fName: str,
        lName: str,
        email: str,
        password: str) -> str:
    uid = shortuuid.uuid()
    query = """
    insert in graph %s {
       ssu:%s a foaf:Person ;
           rdfs:label "%s" ; 
           foaf:firstName "%s" ;
           foaf:lastName "%s" ;
           foaf:mbox "%s" ;
           schema:accessCode "%s" ;
           sso:status "active" .
    }
    """ % (ssu, uid, uid, fName, lName, email, hash_password(password))

    return build(query)


def get_reaction(token: str, course: str):
    query = """
    select ?user ?reaction 
    where {
        graph %s {
            [] a sso:Token ;
                rdfs:seeAlso ?user ;
                rdf:value "%s" .
        }
        optional {
            graph %s {
                values ?reaction { sso:likes sso:dislikes }
                ?user ?reaction %s .
            }
        }
    }
    """ % (sst, token, ssu, course)

    return build(query)


def update_password(token: str, password: str):
    query = """
    modify %s 
    delete { ?s schema:accessCode ?o }
    insert { ?s schema:accessCode "%s" }
    where {
        graph %s {
            [] a sso:Token ;
                rdfs:seeAlso ?s ;
                rdf:value "%s" .
        }
        graph %s {
            ?s schema:accessCode ?o .
        }
    }
    """ % (ssu, hash_password(password), sst, token, ssu)

    return build(query)
