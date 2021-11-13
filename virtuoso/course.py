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


if __name__ == '__main__':
    u = 'http://192.168.0.4:8890/sparql'
    s = core.Session(u)
    # print(create(s, 'desroot'))
    print(create(s, **{'schema:name': '"ACCO23012"'}))
    # print(create(s, 'desroot', 'rani123', 'rani', 'rafid', 'ranii.rafid@gmail.com'))
