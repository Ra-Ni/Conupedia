from configparser import ConfigParser, ExtendedInterpolation
from starlette.templating import Jinja2Templates
import pandas as pd

config = ConfigParser(interpolation=ExtendedInterpolation())
config.read('config.ini')

__buff = config['Sparql']
SPARQL = f'http://{__buff["IP"]}:{__buff["Port"]}{__buff["Path"]}'

__buff = pd.read_html(SPARQL + '?help=nsdecl')[0]
NAMESPACE_PREFIX = '\n'.join(('prefix ' + __buff['Prefix'] + ': <' + __buff['URI'] + '>').to_list())

__buff.index = __buff['Prefix']
NAMESPACES = __buff['URI'].to_dict()

__buff.index = __buff['URI']
NAMESPACES_REVERSED = __buff['Prefix'].to_dict()

__buff = config['Uvicorn']
SERVER_IP = __buff['IP']
SERVER_PORT = int(__buff['Port'])

__buff = config['Web']
WEB_ROOT = __buff['RootDir']
WEB_ASSETS = __buff['Assets']

__buff = config['Graphs']
SSU = __buff['ssu']
SSO = __buff['sso']
SST = __buff['sst']
SSC = __buff['ssc']

TEMPLATES = Jinja2Templates(directory=WEB_ROOT)

del __buff
del config
