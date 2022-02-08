from typing import Optional

from . import Thing


class Rating(Thing):
    def __init__(self, uri: Optional[str] = None,
                 id: Optional[str] = None,
                 owner: Optional[str] = None,
                 subject: Optional[str] = None,
                 value: Optional[str] = None):
        super().__init__(base_prefix='ssr:', type='sso:Rating', uri=uri)
        self._predicates.update({
            'id': id,
            'owner': owner,
            'subject': subject,
            'value': value
        })

    def to_rdf(self, exclude: list = None):

        for key, prefix in [('owner', 'ssu:'), ('subject', 'ssc:')]:
            value = self._predicates.get(key, None)
            if not value or value.startswith('?'):
                continue

            if ':' not in value:
                self._predicates[key] = prefix + value

        return super().to_rdf(exclude)
