import re
import urllib.parse
from json import JSONDecodeError

import requests
import pandas as pd

_SPARQL_ENDPOINT = 'http://192.168.222.128:8890/sparql'
_SPARQL_HEADERS = {
    'Host': '192.168.222.128:8890',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    'Referer': 'http://192.168.222.128:8890/sparql',
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'en-CA,en-GB;q=0.9,en-US;q=0.8,en;q=0.7',
    'Connection': 'Closed'
}
_SPARQL_QUERY = {
    'default-graph-uri': '',
    'query': '',
    'format': 'application/sparql-results+json',
    'timeout': '0',
    'debug': 'on'
}


def get(**kwargs):
    default_args = _SPARQL_QUERY.copy()
    default_args.update(kwargs)

    query_string = ''
    for key, value in default_args.items():
        query_string = query_string + '&' + re.sub('_', '-', key) + '=' + urllib.parse.quote_plus(value)

    query_string = '?' + query_string[1:]

    response = requests.get(_SPARQL_ENDPOINT + query_string, headers=_SPARQL_HEADERS)
    if response.status_code == 200:
        try:
            response = response.json()
            response = response['results']['bindings']
            parsed_response = {}
            for entry in response:  # this is a dictionary object containing key (variables) and dict of value
                for key, value in entry.items():
                    parsed_response.setdefault(key, [])
                    parsed_response[key].append(value['value'])
            return pd.DataFrame.from_dict(parsed_response)
        except JSONDecodeError:
            pass



    return pd.DataFrame()

