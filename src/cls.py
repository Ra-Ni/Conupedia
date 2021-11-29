from configparser import ConfigParser, ExtendedInterpolation
import uvicorn
from app.main import app
from app.internals.globals import SERVER_IP, SERVER_PORT

if __name__ == '__main__':

    uvicorn.run(app, host=SERVER_IP, port=SERVER_PORT)