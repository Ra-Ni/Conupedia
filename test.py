import requests

if  __name__ == '__main__':
    uri = 'https://dbpedia.org/sparql'
    body = {'query':'select distinct ?Concept where {[] a ?Concept} LIMIT 100'}
    headers = {
        'Content-Type': 'text/turtle',
        'Content-Length': str(len(body)),
        'Host': 'https://dbpedia.org/',
        'User-Agent': 'Me',
        'Accept': '*/*'
    }

    response = requests.post(uri, headers=headers, data=body)
    print(response.status_code)
    print(response.text)