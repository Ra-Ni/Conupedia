import pickle

import numpy as np
import pandas as pd
import scipy.sparse as sp
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def transform_data(data_combine, data_plot):
    # count = CountVectorizer(stop_words='english')
    # count_matrix = count.fit_transform(data_combine['combine'])

    tfidf = TfidfVectorizer(stop_words='english')
    tfidf_matrix = tfidf.fit_transform(data_plot['descriptions'])


    # combine_sparse = sp.hstack([count_matrix, tfidf_matrix], format='csr')

    cosine_sim = cosine_similarity(tfidf_matrix, tfidf_matrix)

    return cosine_sim

if __name__ == '__main__':
    with open('../assets/topic_desc.pickle', 'rb') as file:
        topics = pickle.load(file)

    cos_sim = transform_data(None, topics)
    comp445 = cos_sim[1862, :]
    comp445 = list(zip(range(len(comp445)), comp445))
    comp445.sort(key=lambda x: x[1], reverse=True)

    print(comp445)
    print(cos_sim[5464,:])


