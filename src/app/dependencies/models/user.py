from typing import Optional

from . import Thing


class User(Thing):
    def __init__(self, uri: Optional[str] = None,
                 id: Optional[str] = None,
                 first_name: Optional[str] = None,
                 last_name: Optional[str] = None,
                 email: Optional[str] = None,
                 password: Optional[str] = None,
                 status: Optional[str] = None,
                 likes: Optional[str] = None,
                 dislikes: Optional[str] = None):
        super().__init__(base_prefix='ssu:', type='foaf:Person', uri=uri)
        self._predicates.update({
            'id': id,
            'first_name': first_name,
            'last_name': last_name,
            'email': email,
            'password': password,
            'status': status,
            'likes': likes,
            'dislikes': dislikes
        })
