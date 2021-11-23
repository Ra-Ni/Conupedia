import uuid

from .core import Session
from .namespace import PREFIX, SSU


def create(session: Session, user: str):
    token = str(uuid.uuid4())

    query = """
    %s
    insert in graph %s {
        ssu:%s sso:hasSession "%s" .
    }
    """ % (PREFIX, SSU, user, token)
    session.post(query=query)
    return token


def get(session: Session, user: str):
    query = """
    %s
    with %s
    select ?token {
        ssu:%s sso:hasSession ?token
    }
    """ % (PREFIX, SSU, user)
    retval = session.post(query=query)
    return retval[0]['token']


def delete(session: Session, user: str = None, token: str = None) -> list:
    if not (bool(user) or bool(token)):
        raise Exception('Token or user not provided')

    suffix = []
    if user:
        suffix.append(f'?user = ssu:{user}')
    if token:
        suffix.append(f'?token = "{token}"')

    if suffix:
        suffix = 'filter (' + ' && '.join(suffix) + ')'

    query = """
    %s
    with %s
    delete { ?user sso:hasSession ?token }
    where { 
        ?user sso:hasSession ?token 
        %s
    }
    """ % (PREFIX, SSU, suffix)

    return session.post(query=query)



if __name__ == '__main__':
    u = 'http://192.168.0.4:8890/sparql'
    s = Session(u)
    # print(create(s, 'desroot'))
    print(get(s, user='rani'))
    # print(create(s, 'desroot', 'rani123', 'rani', 'rafid', 'ranii.rafid@gmail.com'))
