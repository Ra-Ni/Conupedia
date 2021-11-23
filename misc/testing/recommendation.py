import pickle
import re

from IPython.core.display import display
from rdflib import Graph, URIRef, Literal, Namespace
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def matrix(data):
    tfidf = TfidfVectorizer(stop_words='english')
    tfidf_matrix = tfidf.fit_transform(data)
    cosine_sim = cosine_similarity(tfidf_matrix, tfidf_matrix)

    return cosine_sim


def top_k(data: list, k=10):
    indexed_data = list(enumerate(data))
    indexed_data.sort(key=lambda x: x[1], reverse=True)
    return indexed_data[1:k + 1]


def map_index(indices: dict, data: list):
    return [(indices[index], score) for index, score in data]


if __name__ == '__main__':
    # with open('../../assets/topic_desc.pickle', 'rb') as file:
    #     topics = pickle.load(file)
    # g = Graph()
    # schema = Namespace('http://schema.org/')
    # g.bind('schema', schema)
    # for _, row in topics.iterrows():
    #     dict_items = dict(row)
    #     course = re.sub('http://www.conupedia.sytes.net/Course', 'http://www.securesea.ca/conupedia/course', dict_items['course'])
    #     course = URIRef(course)
    #     description = re.sub('\r', '', dict_items['descriptions'])
    #     description = Literal(description)
    #     if description:
    #         g.add((course, schema.description, description))
    #
    # g.serialize(destination='output.ttl', format='turtle')

    with open('../assets/topic_desc.pickle', 'rb') as file:
        topics = pickle.load(file)

    # topics['course'] = topics['course'].str.replace('securesea.ca', 'www.securesea.ca', regex=True)
    # with open('../assets/topic_desc.pickle', 'wb') as file:
    #      pickle.dump(topics, file)

    courses = dict(topics['course'])
    similarity = matrix(topics['descriptions'])
    scores = dict()
    g = Graph()
    total = []



    for index, course in courses.items():
        rel_similarity = similarity[:, index]
        rel_similarity = top_k(rel_similarity)
        results = [f"\trdfs:seeAlso <{courses[index]}> ;" for index, _ in rel_similarity]
        results = '\n'.join(results)
        results = f'<{courses[index]}>\n' + results[:-1] + '.'
        total.append(results)

    total = '\r\n'.join(total)
    with open('../model/artifacts/similarity.ttl', 'w') as file:
        file.write(total)
