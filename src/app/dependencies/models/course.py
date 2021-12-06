from typing import Optional

from . import Thing


class Course(Thing):
    def __init__(self, uri: Optional[str] = None,
                 id: Optional[str] = None,
                 code: Optional[str] = None,
                 title: Optional[str] = None,
                 credit: Optional[str] = None,
                 description: Optional[str] = None,
                 requisite: Optional[str] = None,
                 degree: Optional[str] = None,
                 similar: Optional[str] = None,
                 dateCreated: Optional[str] = None):
        super().__init__(base_prefix='ssc:', type='schema:Course', uri=uri)
        self._predicates.update({
            'id': id,
            'code': code,
            'title': title,
            'credit': credit,
            'description': description,
            'requisite': requisite,
            'degree': degree,
            'similar': similar,
            'dateCreated': dateCreated
        })
