import hashlib
import re
from io import StringIO

import httpx
import pandas as pd

from app.internals.globals import SPARQL
from app.internals.namespaces import prefix, reverse_namespaces


def build(query, **kwargs):
    query = f'{prefix}\n{query}'
    request = {
        'default-graph-uri': '',
        'query': query,
        'format': 'text/csv; charset=UTF-8',
        'should-sponge': '',
        'signal_void': 'on',
        'signal_unconnected': 'on',
        'timeout': '0',
    }

    request.update(kwargs)
    return request


def hash_password(password: str) -> str:
    h = hashlib.sha256()
    h.update(password.encode())
    return h.hexdigest()


def to_namespaces(resource):
    if not isinstance(resource, str):
        return resource

    match = re.match(r'http://.*[/#]', resource)

    if not match:
        return resource

    match = match.group()

    if match not in reverse_namespaces:
        return resource

    return resource.replace(match, f'{reverse_namespaces[match]}:')


def to_frame(response):
    if response.status_code == 400:
        raise AttributeError('Invalid Request')

    frame = pd.read_csv(StringIO(response.text))
    frame = frame.applymap(to_namespaces)
    return frame


async def send(client: httpx.AsyncClient, query: str, format=None):
    query = build(query)
    response = await client.get(SPARQL, params=query)
    if not format:
        return
    response = to_frame(response)

    if format == 'pandas':
        return response
    elif format == 'dict':
        if response.empty:
            return {}
        return response.to_dict('records')[0]
    elif format == 'records':
        return response.to_dict('records')
    elif format == 'bool':
        return not response.empty and bool(response.iat[0, 0])
    elif format == 'var':
        if response.empty:
            return ''
        return response.iat[0, 0]
    else:
        raise NotImplementedError('Format %s has not been implemented' % format)
