import json

from fastapi import APIRouter, Response
from starlette import status
from starlette.responses import RedirectResponse

from . import user

router = APIRouter()


@router.get('/activate')
async def get(id: str):
    response = await user.get(id)
    if response.status_code != status.HTTP_200_OK:
        return response

    profile = json.loads(response.body)
    status_ = profile['status']
    if status_ != 'inactive':
        return Response(status_code=status.HTTP_403_FORBIDDEN)

    await user.patch(id, status_='member')
    return RedirectResponse(url='/login', status_code=status.HTTP_302_FOUND)
