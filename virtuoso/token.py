import uuid
import datetime

from virtuoso import core


def create(session: core.Session, user: str) -> list:
    uid = uuid.uuid4()
    expiry_date = datetime.datetime.now().replace(microsecond=0) + datetime.timedelta(days=1)

    query = """
    insert in graph <http://www.securesea.ca/conupedia/token/> {
        sst:%s a sso:Token ;
            sso:expires "%s" ;
            rdfs:seeAlso ssu:%s .
    }
    """ % (uid, expiry_date, user)
    return session.post(query=query)


def delete(session: core.Session, **kwargs) -> list:
    if 'user' in kwargs:
        query = """
        with <http://www.securesea.ca/conupedia/token/>
        delete { ?s ?p ?o }
        where { 
            ?s rdfs:seeAlso ssu:%s ;
                ?p ?o .
        }
        """ % kwargs['user']

    elif 'token' in kwargs:
        query = """
        with <http://www.securesea.ca/conupedia/token/>
        delete { sst:%s ?p ?o }
        where { sst:%s ?p ?o }
        """ % (kwargs['token'], kwargs['token'])

    else:
        return []

    return session.post(query=query)


def get(session: core.Session, **kwargs) -> list:
    if 'user' in kwargs:
        query = """
        with <http://www.securesea.ca/conupedia/token/>
        select *
        where {
            ?token a sso:Token ;
                sso:expires ?expiry_date ;
                rdfs:seeAlso ssu:%s .
        }  
        """ % kwargs["user"]

    elif 'token' in kwargs:
        query = """
        with <http://www.securesea.ca/conupedia/token/>
        select *
        where {
            sst:%s a sso:Token ;
                rdfs:seeAlso ?user ;
                sso:expires ?expiry_date .
        }     
        """ % kwargs["token"]
    else:
        return []

    return session.post(query=query)


if __name__ == '__main__':
    u = 'http://192.168.0.4:8890/sparql'
    s = core.Session(u)
    # print(create(s, 'desroot'))
    print(get(s, user='rani'))
    # print(create(s, 'desroot', 'rani123', 'rani', 'rafid', 'ranii.rafid@gmail.com'))
