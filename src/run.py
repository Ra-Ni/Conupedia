import uvicorn

from app.internals.globals import SERVER_IP, SERVER_PORT
from app.main import app

if __name__ == '__main__':
    uvicorn.run(app, host=SERVER_IP, port=SERVER_PORT)
