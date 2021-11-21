from datetime import datetime
import uuid

from virtuoso import core
from virtuoso.namespace import *


def create(session: core.Session, **kwargs) -> list:
    course = uuid.uuid4()
    date = datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
    triples = ';'.join([f'{k} {v}' for k, v in kwargs.items()])

    query = """
    %s
    insert in graph %s {
    ssc:%s rdf:type schema:Course ;
        schema:dateCreated "%s"^^xsd:dateTime ;
        %s .
    }
    """ % (PREFIX, SSC, course, str(date), triples)

    return session.post(query=query)


def delete(session: core.Session, course: str) -> list:
    query = """
    %s
    with %s
    delete { ssc:%s ?p ?o }
    where { ssc:%s ?p ?o }
    """ % (PREFIX, SSC, course, course)

    return session.post(query=query)


def get(session: core.Session, **kwargs) -> list:
    raise NotImplemented


def seen(session: core.Session, user: str) -> set:
    query = """
    %s
    with %s
    select ?course where {
        ssu:%s sso:saw ?course . 
    }
    """ % (PREFIX, SSU, user)

    courses = session.post(query=query)
    if not courses:
        return set()

    courses = set([result['course'] for result in courses])
    return courses


def unseen(session: core.Session, user: str) -> list:
    query = """
    %s
    select ?course where {
        ?course a schema:Course .
        filter not exists { ssu:%s sso:saw ?course . }
    }
    """ % (PREFIX, user)
    courses = session.post(query=query)
    courses = [course['course'] for course in courses]
    return courses


def mark(session: core.Session, user: str, course: str, cmd: str):
    query = """
    %s
    insert in graph %s {
    ssu:%s sso:%s ssc:%s .
    }
    """ % PREFIX, SSU, user, cmd, course
    session.post(query=query)


def recommend(session: core.Session, user: str):
    query = """
    %s
    select distinct ?course where {
        ssu:%s sso:likes ?c .
        ?c rdfs:seeAlso ?course .
        filter not exists { ssu:%s sso:likes ?course . }
    }
    """ % (PREFIX, user, user)

    courses = session.post(query=query)
    return [item['course'] for item in courses]


def popular(session: core.Session):
    query = """
    %s
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
            limit 50
        }
    }
    """ % PREFIX
    return session.post(query=query)


def latest(session: core.Session, threshold: int = 50):
    query = """
    %s
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
    } 
    order by desc(?date) 
    limit %s 
    """ % (PREFIX, threshold)

    return session.post(query=query)

def explore(session: core.Session, user: str, threshold: int = 50):
    query = """
    %s
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
        filter not exists { ssu:%s ?p ?c }
    } 
    order by rand()
    limit %s 
    
    """ % (PREFIX, user, threshold)
    return session.post(query=query)
if __name__ == '__main__':
    u = 'http://192.168.0.4:8890/sparql'
    s = core.Session(u)
    # print(create(s, 'desroot'))
    # print(create(s, **{'schema:name': '"ACCO23012"'}))
    # print(unseen(s, 'desroot'))
    # print(create(s, **{'schema:name': '"ACCO23012"'}))
    # print(latest(s))
    #print(recommend(s, 'desroot'))
    print(explore(s, ''))
