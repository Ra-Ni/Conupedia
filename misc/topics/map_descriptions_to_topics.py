import concurrent
import pickle
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import pandas as pd
from IPython.core.display import display

_TOPIC_DESCRIPTIONS = dict()
_THREADS = 20

def _transform_topics(data):
    documents = []
    for topic_chunk in data['topics']:
        document = []
        for topic in topic_chunk:
            document.append(_TOPIC_DESCRIPTIONS[topic])
        documents.append('\r\n\r\n'.join(document))

    result = data.copy(True)
    result['descriptions'] = documents
    result.drop('topics', axis=1, inplace=True)
    return result

if __name__ == '__main__':
    with open('../assets/descriptions.pickle', 'rb') as file:
        topic_descriptions = pickle.load(file)

    with open('../assets/topics.pickle', 'rb') as file:
        topics = pickle.load(file)


    _TOPIC_DESCRIPTIONS.update(dict(zip(topic_descriptions['topic'], topic_descriptions['descriptions'])))

    parted_topics = np.array_split(topics, _THREADS)
    result = []
    with ThreadPoolExecutor(max_workers=_THREADS) as executor:
        futures = [executor.submit(_transform_topics, topic_chunk) for topic_chunk in parted_topics]

        for fut in concurrent.futures.as_completed(futures):
            result.append(fut.result())

    result = pd.concat(result)
    result.sort_index(inplace=True)

    with open('../assets/topic_desc.pickle', 'wb') as file:
        pickle.dump(result, file)

    result.to_excel('../assets/topic_desc.xlsx')


