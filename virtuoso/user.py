from virtuoso import core


def create(session: core.Session,
           username: str,
           password: str,
           fName: str,
           lName: str,
           email: str) -> list:
    query = """
    insert in graph <http://www.securesea.ca/conupedia/user/> {
        ssu:%s a rdfs:Class ;
            rdfs:subClassOf foaf:Person ;
            schema:accessCode "%s" ;
            foaf:firstName "%s" ;
            foaf:lastName "%s" ;
            foaf:mbox "%s" .
    }
    """ % (username, password, fName, lName, email)

    return session.post(query=query)


def delete(session: core.Session, user: str) -> list:
    query = """
    with <http://www.securesea.ca/conupedia/user/> 
    delete { ssu:%s ?p ?o }
    where { ssu:%s ?p ?o }
    """ % (user, user)

    return session.post(query=query)


def get(session: core.Session, user: str) -> list:
    query = """
    with <http://www.securesea.ca/conupedia/user/>
    select *
    where {
        ssu:%s a rdfs:Class ;
            rdfs:subClassOf foaf:Person ;
            schema:accessCode ?password ;
            foaf:firstName ?fName ;
            foaf:lastName ?lName ;
            foaf:mbox ?email .
    }
    """ % user

    return session.post(query=query)


if __name__ == '__main__':
    u = 'http://192.168.0.4:8890/sparql'
    s = core.Session(u)
    print(get(s, 'desroot'))
    print(delete(s, 'desroot'))
    print(create(s, 'desroot', 'rani123', 'rani', 'rafid', 'ranii.rafid@gmail.com'))
