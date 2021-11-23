from virtuoso import Session


class RatingManager:
    def __init__(self, session: Session):
        self._session = session

    def get(self, course: str, user: str):
        query = """
        %s
        select ?rating
        where {
            %s sso:hasRating ?r .
            
            ?r rdf:value ?value .  
        }
        """ % (SUFFIX, user, )