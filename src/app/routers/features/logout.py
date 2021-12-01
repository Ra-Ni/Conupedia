from fastapi import APIRouter
from starlette.responses import RedirectResponse

router = APIRouter()


@router.get('/logout')
async def logout():
    response = RedirectResponse(url='/login')
    response.delete_cookie(key='token')
    return response
