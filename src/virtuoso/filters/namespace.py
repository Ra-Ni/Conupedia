import re

import pandas as pd

from virtuoso.namespace import namespaces, reverse_namespaces


def _to_namespaces(resource):
    match = re.match(r'http://.*[/#]', resource)

    if not match:
        return resource

    match = match.group()

    if match not in reverse_namespaces:
        return resource

    return resource.replace(match, f'{reverse_namespaces[match]}:')


def namespace(data: pd.DataFrame):
    return data.applymap(_to_namespaces)


