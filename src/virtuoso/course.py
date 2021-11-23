import re

from .core import Session
from .namespace import PREFIX, SSU

class CourseManager:
    def __init__(self, session: Session):
        self._session = session

    def get(self, user: str, predicate: str = None) -> list:
        suffix = '' if not filter else f'filter (?property = sso:{predicate})'

        query = """
        %s
    
         select ?course ?code ?title ?credits ?partOf ?description where {
            %s ?property ?c .
            ?c rdfs:label ?course ;
                schema:courseCode ?code ;
                schema:name ?title ;
                schema:numberOfCredits ?credits ;
                schema:isPartOf ?partOf ;
                schema:description ?description .
            %s
        }
        """ % (PREFIX, user, suffix)

        retval = self._session.post(query=query)
        return retval


    def mark(self, user: str, course: str, cmd: str):
        query = """
        %s
        insert in graph %s {
        ssu:%s sso:%s ssc:%s .
        }
        """ % PREFIX, SSU, user, cmd, course
        self._session.post(query=query)


    def recommend(self, user: str, threshold: int = 50):
        query = """
        %s
        select distinct ?course ?code ?title ?credits ?partOf ?description 
        where {
            %s sso:likes ?o .
            ?o rdfs:seeAlso ?c .
            ?c  rdfs:label ?course ;
                schema:courseCode ?code ;
                schema:name ?title ;
                schema:numberOfCredits ?credits ;
                schema:isPartOf ?partOf ;
                schema:description ?description .
            filter not exists { %s [] ?c }
        } 
        group by ?course 
        order by rand()
        limit %s
        """ % (PREFIX, user, user, threshold)

        return self._session.post(query=query)


    def popular(self, threshold: int = 50):
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
                limit %s
            }
        }
        """ % (PREFIX, threshold)
        return self._session.post(query=query)


    def latest(self, user: str, threshold: int = 50):
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
        filter not exists { %s [] ?c }
        } 
        order by desc(?date) 
        limit %s 
        """ % (PREFIX, user, threshold)

        return self._session.post(query=query)


    def explore(self, user: str, threshold: int = 50):
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
            filter not exists { %s [] ?c }
        } 
        order by rand()
        limit %s 
        
        """ % (PREFIX, user, threshold)
        return self._session.post(query=query)


    def rating(self, user: str, course: str):
        query = """
        %s
        with %s
        select ?property 
        where { ssu:%s ?property ssc:%s }
        """ % (PREFIX, SSU, user, course)

        retval = self._session.post(query=query)
        if not retval:
            return 0

        retval = re.sub(r'.*[/#]', '', retval[0]['property'])
        if retval == 'likes':
            return 2
        elif retval == 'dislikes':
            return 1

        return 0


    def remove_rating(self, user: str, course: str):
        query = """
        %s
        with %s
        delete { ssu:%s ?p ssc:%s }
        where { ssu:%s ?p ssc:%s }
        """ % (PREFIX, SSU, user, course, user, course)
        self._session.post(query=query)


    def add_rating(self, user: str, course: str, rating: str):
        if rating == '1':
            rating = 'dislikes'
        elif rating == '2':
            rating = 'likes'
        else:
            return

        query = """
        %s
        insert in graph %s { ssu:%s sso:%s ssc:%s }
        """ % (PREFIX, SSU, user, rating, course)
        self._session.post(query=query)


if __name__ == '__main__':
    u = 'http://192.168.0.4:8890/sparql'
    s = Session(u)
    # print(create(s, 'desroot'))
    # print(create(s, **{'schema:name': '"ACCO23012"'}))
    # print(unseen(s, 'desroot'))
    # print(create(s, **{'schema:name': '"ACCO23012"'}))
    # print(latest(s))
    # print(recommend(s, 'desroot'))
    print(explore(s, ''))
