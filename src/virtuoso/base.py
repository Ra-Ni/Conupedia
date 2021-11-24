import asyncio
import re
from collections import defaultdict
from io import StringIO

import httpx
import rdflib
from rdflib import URIRef, Literal, BNode, Graph, Variable
import pandas as pd

__all__ = ['Session']

from virtuoso.namespace import reverse_namespaces


class Session:
    def __init__(self, base_url, endpoint, **params):
        self._base_url = base_url
        self._endpoint = endpoint
        self._metadata = {
            'default-graph-uri': '',
            'query': '',
            'format': 'text/csv; charset=UTF-8',
            'should-sponge': '',
            'signal_void': 'on',
            'signal_unconnected': 'on',
            'timeout': '0',
        }
        self._metadata.update(params)

    async def get(self, query):
        response = await self._send_request(query, 'get')
        return response

    async def post(self, query):
        response = await self._send_request(query, 'post')
        return response

    async def _send_request(self, query, method):
        metadata = self._metadata.copy()
        metadata['query'] = query

        async with httpx.AsyncClient(base_url=self._base_url) as client:
            if method == 'get':
                response = await client.get(self._endpoint, params=metadata)

            elif method == 'post':
                response = await client.post(self._endpoint, data=metadata)

            else:
                raise NotImplementedError('No post or get method')

        if response.status_code == 400:
            raise AttributeError('Following query is not valid:\n%s' % query)

        frame = pd.read_csv(StringIO(response.text))
        frame = frame.applymap(to_namespaces)
        # frame = frame.applymap(lambda x: x if type(x) != str or 'http' not in x else f'<{x}>')

        return frame


def to_namespaces(resource):
    match = re.match(r'http://.*[/#]', resource)

    if not match:
        return resource

    match = match.group()

    if match not in reverse_namespaces:
        return resource

    return resource.replace(match, f'{reverse_namespaces[match]}:')



if __name__ == '__main__':
    async def test():
        s = Session("http://192.168.0.7:8890", '/sparql')
        query = 'select * where { ?s ?p ?o }'

        r = await s.get(query)
        print(r)


    loop = asyncio.get_event_loop()
    loop.run_until_complete(test())
    g = Graph()
    s = URIRef('')
    p = Literal('')
    o = Variable('s')
    g.add((s, p, o))
    print(g.serialize())
