from configparser import ConfigParser, ExtendedInterpolation

import uvicorn

import app
from app.main import app
if __name__ == '__main__':

    config = ConfigParser(interpolation=ExtendedInterpolation())
    config.read('config.ini')

    sparql = config['Sparql']
    URI = f'http://{sparql["IP"]}:{sparql["Port"]}'
    PATH = sparql["RelativePath"]

    server = config['Uvicorn']
    uvicorn.run(app, host=server['IP'], port=int(server['Port']))