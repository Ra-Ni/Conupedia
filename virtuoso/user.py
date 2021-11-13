import re
from collections import defaultdict

from virtuoso import core


def create(session: core.Session,
           user: str,
           password: str,
           fName: str,
           lName: str,
           email: str) -> tuple:
    query = """
    insert in graph <http://www.securesea.ca/conupedia/user/> {
        ssu:%s a rdfs:Class ;
            rdfs:subClassOf foaf:Person ;
            schema:accessCode "%s" ;
            foaf:firstName "%s" ;
            foaf:lastName "%s" ;
            foaf:mbox "%s" .
    }
    """ % (user, password, fName, lName, email)
    retval = session.post(query=query)
    return retval != [], {'user': user, 'password': password, 'fName': fName, 'lName': lName, 'email': email}




def delete(session: core.Session, user: str) -> None:
    query = """
    with <http://www.securesea.ca/conupedia/user/> 
    delete { ssu:%s ?p ?o }
    where { ssu:%s ?p ?o }
    """ % (user, user)

    session.post(query=query)


def get(session: core.Session, user: str) -> dict:
    query = """
    with <http://www.securesea.ca/conupedia/user/>
    select *
    where {
        ssu:%s ?p ?o .
    }
    """ % user
    response = session.post(query=query)
    retval = defaultdict(list)
    for item in response:
        key = re.sub('.*[/#](.*)', r'\1', item['p'])
        retval[key].append(item['o'])

    return retval


def insert(session: core.Session, user: str, action: str, course: str):
    query = """
    insert in graph <http://www.securesea.ca/conupedia/user/> {
        ssu:%s sso:%s ssc:%s .
    }
    """ % (user, action, course)

    return session.post(query=query)

def exists(session: core.Session, user: str) -> bool:
    query = """
    select ?user where {
        ?user rdfs:subClassOf foaf:Person .
        FILTER(?user = ssu:%s) .
    }
    """ % user

    return session.post(query=query) != []

if __name__ == '__main__':
    u = 'http://192.168.0.4:8890/sparql'
    s = core.Session(u)
    print(get(s, 'desroot'))
    print(delete(s, 'desroot'))
    print(exists(s, 'desroot'))
    print(create(s, 'desroot', 'rani123', 'rani', 'rafid', 'ranii.rafid@gmail.com'))
    print(insert(s, 'desroot', 'saw', '000537'))

