import uuid
import shortuuid
import re
from virtuoso.core import Session
from virtuoso.namespace import PREFIX, SSU, SST


class InvalidAuthentication(Exception):
    pass


class Authenticator:
    def __init__(self, session: Session):
        self._session = session

    def add(self, user: str) -> str:
        id = shortuuid.uuid()
        token = uuid.uuid4().hex + uuid.uuid4().hex

        query = """
        %s
        insert in graph %s {
            sst:%s a sst:Token ;
                rdfs:label "%s" ;
                rdf:value "%s" ;
                rdfs:seeAlso %s .  
        }
        """ % (PREFIX, SST, id, id, token, user)

        self._session.post(query=query)
        return token

    def delete(self, token: str) -> None:
        if not token:
            raise InvalidAuthentication()

        query = """
        %s
        with %s
        delete { ?s ?p ?o }
        where { ?s ?p ?o ; rdf:value "%s" . }
        """ % (PREFIX, SST, token)
        self._session.post(query=query)

    def get(self, token: str) -> str:
        if not token:
            raise InvalidAuthentication()

        query = """
        %s
        select ?user {
            [] a sst:Token ;
                rdf:value "%s" ;
                rdfs:seeAlso ?user .
        }
        """ % (PREFIX, token)

        user = self._session.post(query=query)
        if not user:
            raise InvalidAuthentication()

        return '<' + user[0]['user'] + '>'


if __name__ == '__main__':
    u = 'http://192.168.0.7:8890/sparql'
    s = Session(u)
    a = Authenticator(s)
    uu = User('123')
    print(a.add(uu))
    # print(create(s, 'desroot'))
    print(get(s, user='rani'))
    # print(create(s, 'desroot', 'rani123', 'rani', 'rafid', 'ranii.rafid@gmail.com'))
