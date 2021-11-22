import re
import uuid
from collections import defaultdict

from virtuoso import core
from virtuoso.namespace import *


def create(session: core.Session,
           fName: str,
           lName: str,
           email: str,
           password: str) -> bool:
    unique_id = str(uuid.uuid4())
    query = """
    %s
    insert in graph %s {
        ssu:%s a rdfs:Class ;
            rdfs:label "%s" ;
            rdfs:subClassOf foaf:Person ;
            foaf:firstName "%s" ;
            foaf:lastName "%s" ;
            foaf:mbox "%s" ;
            schema:accessCode "%s" .
    }
    """ % (PREFIX, SSU, unique_id, unique_id, fName, lName, email, password)
    retval = session.post(query=query)
    return retval != []


def delete(session: core.Session, user: str) -> None:
    query = """
    %s
    with %s 
    delete { ssu:%s ?p ?o }
    where { ssu:%s ?p ?o }
    """ % (PREFIX, SSU, user, user)

    session.post(query=query)


def get(session: core.Session, user: str) -> dict:
    query = """
    %s
    with %s
    select *
    where {
        ssu:%s ?p ?o .
    }
    """ % (PREFIX, SSU, user)
    response = session.post(query=query)
    retval = defaultdict(list)
    for item in response:
        key = re.sub('.*[/#](.*)', r'\1', item['p'])
        retval[key].append(item['o'])

    return retval


def insert(session: core.Session, user: str, action: str, course: str):
    query = """
    %s
    insert in graph %s {
        ssu:%s sso:%s ssc:%s .
    }
    """ % (PREFIX, SSU, user, action, course)

    return session.post(query=query)


def revert_actions(session: core.Session, user: str, course: str):
    query = """
    %s
    with %s 
    delete { ssu:%s ?p ssc:%s }
    where { ssu:%s ?p ssc:%s }
    """ % (PREFIX, SSU, user, course, user, course)
    return session.post(query=query)


def from_email(session: core.Session, email: str):
    query = """
    %s
    with %s
    select ?user ?password where {
        ?user rdfs:subClassOf foaf:Person ;
            foaf:mbox "%s" ;
            schema:accessCode ?password .
    }
    """ % (PREFIX, SSU, email)

    return session.post(query=query)


def exists(session: core.Session, email: str) -> bool:
    query = """
    %s
    select ?user where {
        ?user rdfs:subClassOf foaf:Person ;
            foaf:mbox "%s" .
    }
    """ % (PREFIX, email)

    return session.post(query=query) != []


def from_token(session: core.Session, token: str):
    query = """
    %s
    select ?user 
    where {
    ?user rdfs:subClassOf foaf:Person ;
        sso:hasSession "%s" .
    }
    """ % (PREFIX, token)
    response = session.post(query=query)
    if not response:
        return None
    else:
        return response[0]['user']


def basic_information(session: core.Session, token: str):
    query = """
    %s
    select ?user ?fName ?lName ?email ?password
    where {
        ?u rdfs:subClassOf foaf:Person ;
            rdfs:label ?user ;
            sso:hasSession "%s" ;
            foaf:firstName ?fName ;
            foaf:lastName ?lName ;
            foaf:mbox ?email ;
            schema:accessCode ?password . 
    }
    """ % (PREFIX, token)
    response = session.post(query=query)

    return response[0] if response else None


if __name__ == '__main__':
    u = 'http://192.168.0.4:8890/sparql'
    s = core.Session(u)
    # print(get(s, 'desroot2'))
    # print(delete(s, 'desroot2'))
    # print(exists(s, 'desroot2'))
    # print(create(s, 'desroot2', 'ranii.rafid@gmail.com', 'rani', 'rafid'))
    # print(insert(s, 'desroot2', 'saw', '000055'))
    # print(insert(s, 'desroot2', 'saw', '000043'))
    print(insert(s, 'desroot', 'likes', '000054'))
    # select ?o (count(?o) as ?count) where { [] sso:likes ?o .} group by ?o order by desc(?count)
