import re
import urllib.parse
from json import JSONDecodeError

import requests
from requests import Response

HOST = '192.168.222.128'
PORT = 8890


def session(**kwargs):
    session = requests.Session()
    session.params = {
        'default-graph-uri': '',
        'format': 'application/sparql-results+json',
        'query': '',
        'timeout': '0',
    }
    session.params.update(kwargs)
    session.headers.update(
        {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'en-CA,en-GB;q=0.9,en-US;q=0.8,en;q=0.7',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Connection': 'Keep-Alive'
        }
    )

    return session


def _request(request: str, uri: str, query: str, session: requests.Session) -> dict:
    func_ptr = session.get if request == 'GET' else session.post
    retval = func_ptr(uri + '/sparql', params={'query': query})
    if retval.status_code == 200:
        try:
            return retval.json()
        except JSONDecodeError:
            pass
    return {}


def get(uri: str, query: str, session: requests.Session) -> dict:
    return _request('GET', uri, query, session)


def post(uri: str, query: str, session: requests.Session) -> dict:
    return _request('POST', uri, query, session)


if __name__ == '__main__':
    u = 'https://dbpedia.org'
    q = 'select distinct ?Concept where {[] a ?Concept} LIMIT 100'
    a = {
        'default-graph-uri': 'http://dbpedia.org',
        'timeout': '30000',
        'signal_void': 'on',
        'signal_unconnected': 'on'
    }
    s = session(**a)
    resp = post(u, q, s)
    print(resp)
