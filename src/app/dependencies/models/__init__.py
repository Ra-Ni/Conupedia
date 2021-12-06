import json
from typing import Optional

from ...internals.globals import VOCABULARY


class Thing:

    def __init__(self,
                 base_prefix: Optional[str] = None,
                 uri: Optional[str] = None,
                 type: Optional[str] = None):
        self._uri = uri
        self._base_prefix = base_prefix
        self._predicates = {'type': type}

    def __dict__(self):
        return self._predicates

    def dict(self):
        return self._predicates.copy()

    def to_rdf(self, exclude: list = None):
        results = []
        keys = {k for k, v in self._predicates.items() if v}
        if exclude:
            keys = keys - set(exclude)

        for k in keys:
            v = self._predicates[k]
            if ':' not in v and not v.startswith('?'):
                v = f'"{v}"'

            results.append(f'{VOCABULARY[k]} {v}')

        uri = self._uri
        if not uri:
            uri = '[]'
        elif ':' not in uri and not uri.startswith('?'):
            uri = self._base_prefix + uri

        results = ';'.join(results)
        if results:
            results = f'{uri} {results} .'

        return results

    def vars(self):
        results = []
        for v in self.dict().values():
            if isinstance(v, str) and v.startswith('?'):
                results.append(v)
        return ' '.join(results)

    def fill_var(self, exclude: list = None):
        keys = set(self._predicates.keys())
        if exclude:
            keys = keys - set(exclude)
        for k in keys:
            if not self._predicates[k]:
                self._predicates[k] = f'?{k}'

    def unfill_var(self, exclude: list = None):
        keys = set(self._predicates.keys())
        if exclude:
            keys = keys - set(exclude)
        for k in keys:
            v = self._predicates[k]
            if isinstance(v, str) and v.startswith('?'):
                self._predicates[k] = None

    def to_query(self, exclude: list = None):
        other = self.copy()

        keys = {k for k, v in self._predicates.items() if v}
        if exclude:
            keys = keys - set(exclude)

        for k in keys:
            other._predicates[k] = f'?{k}'

        return other

    def copy(self):
        other = self.__class__()
        other._uri = self._uri
        other._predicates = self._predicates.copy()
        other._base_prefix = self._base_prefix
        return other

    def update(self, other: dict):
        self._predicates.update(other)

    def json(self):
        return json.dumps(self._predicates)

    def truncate(self, keys: list):
        keys = {k for k in self._predicates.keys()} - set(keys)
        for k in keys:
            del self._predicates[k]

    def at(self, key):
        return self._predicates.get(key, None)

    def set(self, key, value):
        self._predicates[key] = value
