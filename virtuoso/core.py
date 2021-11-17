import re
import urllib.parse
from json import JSONDecodeError

import requests
from requests import Response


def _beautify_response(response: requests.Response) -> list:
    try:
        retval = response.json()
        retval = retval['results']['bindings']
        for result in retval:
            for k in result.keys():
                result[k] = result[k]['value']
        return retval
    except JSONDecodeError:
        return []


class Session(requests.Session):
    def __init__(self, uri, **kwargs):
        super().__init__()
        self._uri = uri
        self.params = {
            'default-graph-uri': '',
            'format': 'application/sparql-results+json',
            'query': '',
            'timeout': '0',
        }
        self.params.update(kwargs)
        self.headers.update(
            {
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                'Accept-Encoding': 'gzip, deflate',
                'Accept-Language': 'en-CA,en-GB;q=0.9,en-US;q=0.8,en;q=0.7',
                'Content-Type': 'application/x-www-form-urlencoded',
                'Connection': 'Keep-Alive'
            }
        )

    def get(self, uri=None, **kwargs) -> list:
        target = uri or self._uri
        response = super().get(target, params=kwargs)
        if response.status_code != 200:
            raise Exception('Bad request')

        return _beautify_response(response)

    def post(self, uri=None, **kwargs) -> list:
        target = uri or self._uri
        response = super().post(target, params=kwargs)
        if response.status_code != 200:
            raise Exception('Bad request')

        return _beautify_response(response)

if __name__ == '__main__':
    u = 'http://192.168.0.4:8890/sparql'
    q = 'select distinct ?Concept where {[] a ?Concept} LIMIT 100'

    a = {
        'default-graph-uri': '',
        'timeout': '0',
    }
    s = Session(u, **a)
    resp = s.post(query=q)
    print(resp)
