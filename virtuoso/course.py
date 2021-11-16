import uuid

from virtuoso import core


def create(session: core.Session, **kwargs) -> list:
    course = uuid.uuid4()
    triples = ';'.join([f'{k} {v}' for k, v in kwargs.items()])

    query = """
    insert in graph <http://www.securesea.ca/conupedia/course/> {
    ssc:%s rdf:type schema:Course ;
        %s .
    }
    """ % (course, triples)

    return session.post(query=query)


def delete(session: core.Session, course: str) -> list:
    query = """
    with <http://www.securesea.ca/conupedia/course/> 
    delete { ssc:%s ?p ?o }
    where { ssc:%s ?p ?o }
    """ % course

    return session.post(query=query)


def get(session: core.Session, **kwargs) -> list:
    raise NotImplemented


def seen(session: core.Session, user: str) -> set:
    query = """
    with <http://www.securesea.ca/conupedia/user/>
    select ?course where {
        ssu:%s sso:saw ?course . 
    }
    """ % user

    courses = session.post(query=query)
    if not courses:
        return set()

    courses = set([result['course'] for result in courses])
    return courses


def unseen(session: core.Session, user: str) -> list:
    query = """
    select ?course where {
        ?course a schema:Course .
        filter not exists { ssu:%s sso:saw ?course . }
    }
    """ % user
    courses = session.post(query=query)
    courses = [course['course'] for course in courses]
    return courses


def mark(session: core.Session, user: str, course: str, cmd: str):
    query = """
    insert in graph <http://www.securesea.ca/conupedia/user/> {
    ssu:%s sso:%s ssc:%s .
    }
    """ % user, cmd, course
    session.post(query=query)


def recommend(session: core.Session, user: str):
    query = """
    select ?course where {
        ssu:%s sso:likes ?c .
        ?c rdfs:seeAlso ?course .
        filter not exists { ssu:%s sso:saw ?course . }
    }
    """ % (user, user)

    courses = session.post(query=query)
    return [item['course'] for item in courses]


if __name__ == '__main__':
    u = 'http://192.168.0.4:8890/sparql'
    s = core.Session(u)
    # print(create(s, 'desroot'))
    # print(create(s, **{'schema:name': '"ACCO23012"'}))
    # print(unseen(s, 'desroot'))
    print(recommend(s, 'desroot'))
