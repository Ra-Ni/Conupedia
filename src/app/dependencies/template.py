class Template:
    def __init__(self, **kwargs):
        self._keys = kwargs

    def __str__(self):
        raise NotImplementedError('Function __str__ has not been implemented yet')

