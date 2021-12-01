import httpx
import uvicorn
from fastapi.encoders import jsonable_encoder

from app.dependencies import core
from app.main import app
from app.internals.globals import SERVER_IP, SERVER_PORT, TEMPLATES, SSC
from fastapi import Request


if __name__ == '__main__':

    uvicorn.run(app, host=SERVER_IP, port=SERVER_PORT)