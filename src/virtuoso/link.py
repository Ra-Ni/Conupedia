from virtuoso import Session
from virtuoso.namespace import PREFIX, SSU


class LinkManager:
    def __init__(self, session: Session):
        self._session = session

    def get(self, subject, predicate, target):
        suffix = []
        if subject:
            suffix.append(f'?subject = {subject}')
        if predicate:
            suffix.append(f'?key = {predicate}')
        if target:
            suffix.append(f'?value = {target}')

        suffix = ' && '.join(suffix)
        if suffix:
            suffix = f'filter ( {suffix} )'

        query = """
        %s
        select ?subject ?key ?value
        where { ?subject ?key ?value . %s }
        """ % (PREFIX, suffix)

        return self._session.post(query=query)


    def add(self, subject: str, predicate: str, target: str, context: str = SSU):

        query = """
        %s
        insert in graph %s { 
        %s %s %s .
        }
        """ % (PREFIX, context, subject, predicate, target)

        self._session.post(query=query)

    def delete(self, subject: str, predicate: str, target: str):
        suffix = []
        if subject:
            suffix.append(f'?s = {subject}')
        if predicate:
            suffix.append(f'?p = {predicate}')
        if target:
            suffix.append(f'?o = {target}')

        suffix = ' && '.join(suffix)
        if suffix:
            suffix = f'filter ( {suffix} )'

        query = """
        %s
        with %s
        delete { ?s ?p ?o }
        where { ?s ?p ?o . %s }
        """ % (PREFIX, SSU, suffix)

        self._session.post(query=query)
