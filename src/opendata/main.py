import concurrent
import pickle
from array import array
from concurrent.futures import ThreadPoolExecutor
from configparser import ConfigParser, ExtendedInterpolation
from json import JSONDecodeError

import numpy as np
import pandas as pd
import requests


def get() -> pd.DataFrame:
    response = requests.get(OPENDATA + '/course/catalog/filter/*/*/*', auth=(OPENDATA_USER, OPENDATA_KEY))
    response = response.json()
    catalog = pd.DataFrame(response)
    catalog['subject'] = catalog['subject'] + catalog['catalog']
    catalog['title'] = catalog['title'].apply(lambda x: x.title())
    catalog.index = catalog['ID']
    del catalog['ID']
    del catalog['catalog']
    del catalog['crosslisted']

    response = requests.get(OPENDATA + '/course/description/filter/*', auth=(OPENDATA_USER, OPENDATA_KEY))
    response = response.json()
    description = pd.DataFrame(response)
    description.index = description['ID']
    del description['ID']

    courses = catalog.join(description)
    courses.to_excel('out.xlsx')

    return courses


def dbpedia_spotlight(courses):
    def run(chunk: list):
        retval = chunk.copy()
        for item in retval:
            params = {'text': item['description'], 'confidence': '0.3'}
            headers = {'accept': 'application/json'}
            response = requests.get('localhost:2222/en/annotate', params=params, headers=headers)
            try:
                response = response.json()
                if 'Resources' in response:
                    response = response['Resources']
                    item['keywords'] = [x['@URI'] for x in response]
                else:
                    item['keywords'] = []
            except JSONDecodeError:
                item['keywords'] = []
        return retval

    courses = courses.to_dict('records')
    futures = []
    course_chunks = np.array_split(courses, 20)
    results = []
    executor = ThreadPoolExecutor(max_workers=20)
    for chunk in course_chunks:
        futures.append(executor.submit(run, chunk))

    for future in concurrent.futures.as_completed(futures):
        results.extend(future.result())

if __name__ == '__main__':
    config = ConfigParser(interpolation=ExtendedInterpolation())
    config.read('../config.ini')

    __buff = config['OpenData']
    OPENDATA = __buff['URL']
    OPENDATA_KEY = __buff['Key']
    OPENDATA_USER = __buff['User']

    courses = get()
    results = dbpedia_spotlight(courses)
    with open('out2.pickle', 'wb') as out:
        pickle.dump(results, out)