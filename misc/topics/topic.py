import concurrent.futures
import pickle
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from math import ceil

import sparql
import re
import pandas as pd
import numpy as np


def _extract_keywords(data: str):
    keyword = re.sub(r'.*/', '', data)
    keyword = re.sub(r'_', ' ', keyword)
    return keyword


def _partition(data, number):
    chunk_size = ceil(len(data) / float(number))

    for i in range(0, len(data), chunk_size):
        yield data.iloc[i:i + chunk_size]


def _get_topics(data):
    topics = []
    for course in data['course']:
        query = """
            select ?topic where {
                <%s> owl:sameAs ?topic .
            }
            """ % course
        response = sparql.get(query=query)
        if response.empty:
            topics.append([])
        else:
            topics.append(list(response['topic'].values))

    result = data.copy(True)
    result['topics'] = topics
    return result


def get_topics(threads=20):
    query = """
          select ?course ?title where {
              ?course rdf:type schema:Course ;
                  schema:name ?title .
          }
          """
    response = sparql.get(query=query)

    parted_courses = np.array_split(response, threads)
    result = []
    with ThreadPoolExecutor(max_workers=threads) as executor:
        futures = [executor.submit(_get_topics, course_chunk) for course_chunk in parted_courses]

        for fut in concurrent.futures.as_completed(futures):
            result.append(fut.result())

    result = pd.concat(result)
    result.sort_index(inplace=True)
    return result


def part1():
    query = """
        select ?course ?title where {
            ?course rdf:type schema:Course ;
                schema:name ?title .
        }
        """

    frame = sparql.get(query=query)

    topics = []
    for course in frame['course']:
        query = """
            select ?topic where {
                <%s> owl:sameAs ?topic .
            }""" % (course)
        response = sparql.get(query=query)
        if response.empty:
            topics.append([])
        else:
            topics.append(list(response['topic'].values))

    frame['topics'] = topics

    with open('topics.pickle', 'wb') as file:
        pickle.dump(frame, file)
    frame.to_excel('topics3.xlsx')
    # response['s'] = response['s'].apply(_extract_keywords)
    print(frame)
    # print(response)


def get_description(data, tid):
    topic_descriptions = []
    for resource in data:
        query = """
        select ?abstract where {
            <%s> <http://dbpedia.org/ontology/abstract> ?abstract .
            FILTER (lang(?abstract) = 'en')
        }
        """ % (resource)
        response = sparql.get(query=query, should_sponge='grab-all')
        if response.empty:
            topic_descriptions.append('')
        else:
            topic_descriptions.append(response.iloc[0, 0])

    with open(f'descriptions_{tid}.pickle', 'wb') as file:
        pickle.dump(topic_descriptions, file)

    return topic_descriptions


def part2():
    query = """
    select distinct ?topic where {
        ?c rdf:type schema:Course ;
            owl:sameAs ?topic .
    }"""
    topics = sparql.get(query=query)

    topic_descriptions = []
    print(len(topics))
    threads = 20
    partitions = [x for x in range(0, len(topics), ceil(len(topics) / threads))] + [len(topics)]
    topic_list = list(topics['topic'].values)
    topic_partitions = [topic_list[partitions[i]:partitions[i + 1]] for i in range(threads)]

    executor = ThreadPoolExecutor(max_workers=threads)
    results = []
    for i in range(threads):
        results.append(executor.submit(get_description, topic_partitions[i], i))

    final_result = dict()
    queue = deque(list(range(threads)))

    while queue:
        item = queue.pop()
        if results[item].running():
            queue.appendleft(item)
        elif results[item].cancelled():
            print(f'part#{item} cancelled')
        elif results[item].done():
            print(f'part#{item} done')
            final_result[item] = results[item].result()
    results = dict(sorted(final_result.items()))
    final_result = []

    for key, value in results.items():
        final_result.extend(value)

    topics['descriptions'] = final_result
    with open('descriptions.pickle', 'wb') as file:
        pickle.dump(topics, file)
    topics.to_excel('descriptions.xlsx')


if __name__ == '__main__':
    result = get_topics(20)
    with open('topics.pickle', 'wb') as file:
        pickle.dump(result, file)
    result.to_excel('topics.xlsx')
    print(result)
    #
    # progress_bar = ProgressBar(threshold=len(topics))
    # for topic in topics['topic']:
    #     query = """
    #     select ?abstract where {
    #         <%s> <http://dbpedia.org/ontology/abstract> ?abstract .
    #         FILTER (lang(?abstract) = 'en')
    #     }
    #     """ % (topic)
    #     response = sparql.get(query=query, should_sponge='grab-all')
    #     if response.empty:
    #         topic_descriptions.append('')
    #     else:
    #         topic_descriptions.append(response.iloc[0, 0])
    #     progress_bar.console_update()
    #
    # topics['descriptions'] = topic_descriptions
    # with open('descriptions.pickle', 'wb') as file:
    #     pickle.dump(topics, file)
    # topics.to_excel('descriptions.xlsx')
