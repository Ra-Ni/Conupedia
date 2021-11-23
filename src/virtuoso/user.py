import re
import uuid
import shortuuid
from collections import defaultdict

from virtuoso.core import Session
from virtuoso.namespace import PREFIX, SSU


class UserNotFound(Exception):
    pass


class UserManager:
    def __init__(self, session: Session):
        self._session = session

    def add(self, first_name: str, last_name: str, email: str, password: str):
        id = shortuuid.uuid()
        query = """
        %s
        insert in graph %s {
            ssu:%s a foaf:Person ;
                rdfs:label "%s" ; 
                foaf:firstName "%s" ;
                foaf:lastName "%s" ;
                foaf:mbox "%s" ;
                schema:accessCode "%s" ;
                rdf:value "%s" ;
                sso:status "active" .
        }
        """ % (PREFIX,
               SSU,
               id,
               f'{first_name} {last_name}',
               first_name,
               last_name,
               email,
               password,
               id)
        self._session.post(query=query)
        return id

    def delete(self, user_id: str):
        query = """
        %s
        insert in graph %s {
            ssu:%s sso:status "inactive" .
        }
        """ % (PREFIX, SSU, user_id)

        self._session.post(query=query)

    def get(self, user: str, simplify: bool = False):
        query = """
        %s
        with %s
        select ?key ?value 
        where {
           %s ?key ?value .
        }
        """ % (PREFIX, SSU, user)
        user = self._session.post(query=query)
        if not user or not simplify:
            return user

        simplified = defaultdict(list)
        for item in user:
            key = re.sub(r'.*[/#]', '', item['key'])
            value = re.sub(r'.*[/#]', '', item['value'])
            simplified[key].append(value)
        for item in simplified.keys():
            if len(simplified[item]) == 1:
                simplified[item] = simplified[item][0]
        return simplified


def create(session: Session,
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


def delete(session: Session, user: str) -> None:
    query = """
    %s
    with %s 
    delete { ssu:%s ?p ?o }
    where { ssu:%s ?p ?o }
    """ % (PREFIX, SSU, user, user)

    session.post(query=query)


def get(session: Session, user: str, email: str, simplified: bool = False) -> dict:

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


def insert(session: Session, user: str, action: str, course: str):
    query = """
    %s
    insert in graph %s {
        ssu:%s sso:%s ssc:%s .
    }
    """ % (PREFIX, SSU, user, action, course)

    return session.post(query=query)


def revert_actions(session: Session, user: str, course: str):
    query = """
    %s
    with %s 
    delete { ssu:%s ?p ssc:%s }
    where { ssu:%s ?p ssc:%s }
    """ % (PREFIX, SSU, user, course, user, course)
    return session.post(query=query)


def from_email(session: Session, email: str):
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


def exists(session: Session, email: str) -> bool:
    query = """
    %s
    select ?user where {
        ?user rdfs:subClassOf foaf:Person ;
            foaf:mbox "%s" .
    }
    """ % (PREFIX, email)

    return session.post(query=query) != []


def from_token(session: Session, token: str):
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


def basic_information(session: Session, token: str):
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
    u = 'http://192.168.0.7:8890/sparql'
    s = Session(u)
    uu = UserManager(s)
    print(uu.get('3f05a29f-10cf-4bb4-977c-ec44f04910bf'))
    # print(get(s, 'desroot2'))
    # print(delete(s, 'desroot2'))
    # print(exists(s, 'desroot2'))
    # print(create(s, 'desroot2', 'ranii.rafid@gmail.com', 'rani', 'rafid'))
    # print(insert(s, 'desroot2', 'saw', '000055'))
    # print(insert(s, 'desroot2', 'saw', '000043'))
    # print(insert(s, 'desroot', 'likes', '000054'))
    # select ?o (count(?o) as ?count) where { [] sso:likes ?o .} group by ?o order by desc(?count)
