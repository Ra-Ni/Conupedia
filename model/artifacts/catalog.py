import concurrent
import pickle
import re
from concurrent.futures import ThreadPoolExecutor
from configparser import ConfigParser, ExtendedInterpolation
from http.client import HTTPException
from json import JSONDecodeError

import numpy as np
import pandas as pd
import requests
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def _get_courses():
    response = requests.get(OPENDATA + '/course/catalog/filter/*/*/*', auth=(OPENDATA_USER, OPENDATA_KEY))
    response = response.json()
    catalog = pd.DataFrame(response)
    catalog['subject'] = catalog['subject'] + catalog['catalog']
    catalog['title'] = catalog['title'].apply(lambda x: x.title())
    catalog.index = catalog['ID']
    del catalog['ID']
    del catalog['catalog']
    del catalog['crosslisted']

    catalog.drop_duplicates('title', inplace=True)

    return catalog


def _get_descriptions():
    response = requests.get(OPENDATA + '/course/description/filter/*', auth=(OPENDATA_USER, OPENDATA_KEY))
    response = response.json()
    description = pd.DataFrame(response)
    description.index = description['ID']
    del description['ID']

    return description


def _delete_duds(data: pd.DataFrame):
    patterns = [
        "(?:Please|See) .*alendar\.*|(?:PLEASE )?SEE .*DAR(?:\.)?",
        "\*\*\*(?:PLESE)*",
        "\*VID\*\n*\*KEYB\*\n|\*VID\*\n|\*(?:CNT|APP)\*",
        "\"|\*|\n|\r|^ |~*|<.*>",
        "(?:IMPORTANT )?NOTES?[:-].*|Notes?[:-].*",
        "Prerequisite.*?[\.!\?](?:\s|$)",
        "(?i:...).*Students who have taken.*",
        "(\t|\r\n|\n)",
        "\\\\",
        "(?:Tutorial|Lectures|Laboratory):[^.]*[.]",
    ]
    patterns = '|'.join([f'(?:{x})' for x in patterns])
    patterns = rf'{patterns}'
    patterns = re.compile(patterns)

    for _, row in data.iterrows():
        row['description'] = patterns.sub('', row['description'])


def _get_keywords(data: pd.DataFrame):
    params = {'text': None,
              'confidence': '0.35',
              'support': 0,
              'spotter': 'Default',
              'policy': 'whitelist'}
    headers = {'accept': 'application/json'}
    url = 'https://api.dbpedia-spotlight.org/en/annotate'

    def run(chunk: list):
        for item in chunk:
            _params = params.copy()
            _params['text'] = item['description']
            response = requests.get(url, params=_params, headers=headers)
            try:
                if response.status_code != 200:
                    raise HTTPException(f'Cannot find text or url for {item}')

                response = response.json()

                if 'Resources' in response:
                    response = response['Resources']
                    item['keywords'] = list(set([x['@URI'] for x in response]))
                else:
                    item['keywords'] = []
            except JSONDecodeError:
                item['keywords'] = []
        return True

    data_dict = data.to_dict('records')
    futures = []
    course_chunks = np.array_split(data_dict, 20)
    executor = ThreadPoolExecutor(max_workers=20)

    for chunk in course_chunks:
        futures.append(executor.submit(run, chunk))

    for _ in concurrent.futures.as_completed(futures):
        pass

    executor.shutdown()
    return pd.DataFrame().from_records(data_dict)


def _get_abstracts(data: pd.DataFrame):
    url = 'https://dbpedia.org/sparql/'

    params = {'query': '',
              'format': 'application/sparql-results+json',
              'timeout': '0',
              'signal_void': 'on',
              'signal_unconnected': 'on',
              'default-graph-uri': 'http://dbpedia.org'
              }

    def run(chunk: list):
        try:
            params_ = params.copy()
            for item in chunk:
                result = []
                for keyword in item['keywords']:
                    params_['query'] = """
                    select ?info where {
                    <%s> dbo:abstract ?info
                    filter (lang(?info) = 'en')
                    }
                    """ % keyword

                    response = requests.get(url, params=params_)

                    response.encoding = response.apparent_encoding
                    response = response.json()
                    text = response['results']['bindings']
                    if text:
                        text = text[0]['info']['value']
                        result.append(text)

                item['keyword description'] = '\n'.join(result)
        except Exception:
            print('why')
        return True

    data_dict = data.to_dict('records')
    futures = []
    course_chunks = np.array_split(data_dict, 20)
    executor = ThreadPoolExecutor(max_workers=20)

    for chunk in course_chunks:
        futures.append(executor.submit(run, chunk))

    for _ in concurrent.futures.as_completed(futures):
        pass

    executor.shutdown()
    return pd.DataFrame().from_records(data_dict)


def _get_similarities(data: pd.DataFrame):
    keyword_descriptions = data['keyword description']

    tfidf = TfidfVectorizer(stop_words='english')
    tfidf_matrix = tfidf.fit_transform(keyword_descriptions)
    cosine_sim = cosine_similarity(tfidf_matrix, tfidf_matrix)

    results = []
    for index, row in enumerate(cosine_sim):
        if not data.iloc[index]['keyword description']:
            results.append([])
        else:
            ordering = list(enumerate(row))
            ordering.sort(key=lambda x: x[1], reverse=True)
            ordering = [x for x, _ in ordering[1:]]
            results.append(ordering)

    data['scores'] = results
    return data


if __name__ == '__main__':
    config = ConfigParser(interpolation=ExtendedInterpolation())
    config.read('../config.ini')

    __buff = config['OpenData']
    OPENDATA = __buff['URL']
    OPENDATA_KEY = __buff['Key']
    OPENDATA_USER = __buff['User']

    courses = _get_courses()
    descriptions = _get_descriptions()
    catalog = courses.join(descriptions)

    _delete_duds(catalog)
    catalog.drop(catalog[catalog['description'] == ''].index, inplace=True)
    catalog.drop(catalog[catalog['description'] == ' '].index, inplace=True)

    catalog = _get_keywords(catalog)

    catalog = _get_abstracts(catalog)

    catalog = _get_similarities(catalog)

    catalog.to_excel('catalog.xlsx')
    with open('catalog.pickle', 'wb') as file:
        pickle.dump(catalog, file)
