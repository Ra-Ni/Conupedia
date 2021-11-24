import hashlib
import re
from io import StringIO

import pandas as pd

from virtuoso.namespace import prefix, reverse_namespaces


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
