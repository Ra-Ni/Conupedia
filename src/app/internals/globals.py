from configparser import ConfigParser, ExtendedInterpolation

from starlette.templating import Jinja2Templates

config = ConfigParser(interpolation=ExtendedInterpolation())
config.read('config.ini')

__buff = config['Sparql']
SPARQL = f'http://{__buff["IP"]}:{__buff["Port"]}/{__buff["RelativePath"]}'


__buff = config['Uvicorn']
SERVER_IP = __buff['IP']
SERVER_PORT = __buff['Port']

__buff = config['Web']
WEB_ROOT = __buff['RootDir']
WEB_ASSETS = __buff['Assets']

del __buff

TEMPLATES = Jinja2Templates(directory=WEB_ROOT)
