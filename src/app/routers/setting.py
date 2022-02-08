
from fastapi import APIRouter, Request, Form

from app.dependencies import core
from app.internals.globals import TEMPLATES
from app.routers import user

router = APIRouter()


@router.get('/setting')
async def profile(request: Request):
    user_profile = request.state.user
    context = {'request': request, 'user_profile': user_profile}

    return TEMPLATES.TemplateResponse('setting.html', context=context)


@router.post('/setting')
async def profile(request: Request,
                  current_password: str = Form(...),
                  new_password: str = Form(...),
                  confirm_new_password: str = Form(...)):
    user_profile = request.state.user
    uid = user_profile['id']
    password = user_profile['password']
    context = {'request': request, 'user_profile': user_profile, 'password_feedback': None}

    if password != core.hash_password(current_password):
        context['password_error'] = "Incorrect input for current password."
        return TEMPLATES.TemplateResponse('setting.html', context=context)

    if new_password != confirm_new_password:
        context['password_error'] = "Passwords do not match."
        return TEMPLATES.TemplateResponse('setting.html', context=context)

    new_password = core.hash_password(new_password)
    await user.patch(uid, password=new_password)

    context['password_feedback'] = "Password updated successfully."
    return TEMPLATES.TemplateResponse('setting.html', context=context)
