ssu = '<http://localhost:8890/user>'
sso = '<http://localhost:8890/ontology>'
sst = '<http://localhost:8890/token>'
ssc = '<http://localhost:8890/course>'

prefix = """
prefix sst: <http://localhost:8890/token/> 
prefix sso: <http://localhost:8890/ontology/> 
prefix ssu: <http://localhost:8890/user/> 
prefix ssc: <http://localhost:8890/course/> 

prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> 
prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> 
prefix foaf: <http://xmlns.com/foaf/0.1/> 
prefix xsd: <http://www.w3.org/2001/XMLSchema#> 
prefix dbr: <http://dbpedia.org/resource/> 
prefix owl: <http://www.w3.org/2002/07/owl#> 
prefix schema: <http://schema.org/version/6.0/#> 

"""

namespaces = {
    'ssu': 'http://localhost:8890/user/',
    'sso': 'http://localhost:8890/ontology/',
    'sst': 'http://localhost:8890/token/',
    'ssc': 'http://localhost:8890/course/',
    'rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#',
    'rdfs': 'http://www.w3.org/2000/01/rdf-schema#',
    'foaf': 'http://xmlns.com/foaf/0.1/',
    'xsd': 'http://www.w3.org/2001/XMLSchema#',
    'dbr': 'http://dbpedia.org/resource/',
    'owl': 'http://www.w3.org/2002/07/owl#',
    'schema': 'http://schema.org/version/6.0/#',
}

reverse_namespaces = {
    'http://localhost:8890/user/': 'ssu',
    'http://localhost:8890/ontology/': 'sso',
    'http://localhost:8890/token/': 'sst',
    'http://localhost:8890/course/': 'ssc',
    'http://www.w3.org/1999/02/22-rdf-syntax-ns#': 'rdf',
    'http://www.w3.org/2000/01/rdf-schema#': 'rdfs',
    'http://xmlns.com/foaf/0.1/': 'foaf',
    'http://www.w3.org/2001/XMLSchema#': 'xsd',
    'http://dbpedia.org/resource/': 'dbr',
    'http://www.w3.org/2002/07/owl#': 'owl',
    'http://schema.org/version/6.0/#': 'schema',
}