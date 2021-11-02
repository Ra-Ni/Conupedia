import sparql
from sparql import get
import pandas as pd

if __name__ == '__main__':
    query = """
    select distinct ?t where {
        ?s rdf:type schema:Course ;
        owl:sameAs ?t .
    }
    """
    response = get(query=query)
    # print(response)

    query = """
    select ?s ?t where {
        ?s rdf:type schema:Course ;
        owl:sameAs ?t .
    }
    """
    response = get(query=query)
    response = pd.DataFrame.from_dict(response)
    print(response)