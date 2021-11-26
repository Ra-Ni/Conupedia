from .base import build


def get_popular(user: str, threshold: int = 50):
    query = """
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
    """ % threshold

    return build(query)


def get_latest(user: str, threshold: int = 50):
    query = """
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
    """ % (user, threshold)

    return build(query)


def get_explore(user: str, threshold: int = 50):
    query = """
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
    """ % (user, threshold)

    return build(query)


def get_recommendation(user: str, threshold: int = 50):
    query = """
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
    """ % (user, user, threshold)

    return build(query)


def get_likes(user: str, threshold: int = 50):
    query = """
    select distinct ?course ?code ?title ?credits ?partOf ?description
    where {
        %s sso:likes ?c .
        ?c  rdfs:label ?course ;
            schema:courseCode ?code ;
            schema:name ?title ;
            schema:numberOfCredits ?credits ;
            schema:isPartOf ?partOf ;
            schema:description ?description .
    }
    """ % user

    return build(query)
