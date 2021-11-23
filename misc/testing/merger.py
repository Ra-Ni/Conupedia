from rdflib import Graph
from rdflib.namespace import OWL


def remove_owl(g: Graph):
    g.remove((None, OWL.sameAs, None))

if __name__ == '__main__':
    files = ['../model/course.ttl', '../model/similarity.ttl']
    graph = Graph()

    for file in files:
        graph.parse(file)

    remove_owl(graph)
    graph.serialize('course.ttl', format='turtle')