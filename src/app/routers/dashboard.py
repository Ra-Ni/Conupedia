from typing import Optional
import httpx
from fastapi import APIRouter, Request, Response, Cookie, Form
from starlette import status
from starlette.responses import RedirectResponse
from ..internals.globals import TEMPLATES, SPARQL
from ..virtuoso import users, base, auth, recommendations

router = APIRouter()


@router.get('/dashboard')
async def dashboard(request: Request, sessionID: Optional[str] = Cookie(None)):
    if not sessionID:
        return RedirectResponse(url='/login')

    context = {'request': request, 'categories': {}}
    query = users.from_token(sessionID)

    async with httpx.AsyncClient() as client:
        user = await client.get(SPARQL, params=query)
        user = base.to_frame(user)
        context['user_info'] = user = user.to_dict('records')[0]

        methods = {
            'Recommended': recommendations.get_recommendation,
            'Popular': recommendations.get_popular,
            'Explore': recommendations.get_explore,
            'Latest': recommendations.get_latest,
            'Likes': recommendations.get_likes,
        }
        for title, method in methods.items():
            query = method(user['id'])

            latest = await client.get(SPARQL, params=query)
            latest = base.to_frame(latest)
            context['categories'][title] = latest.to_dict('records')

    return TEMPLATES.TemplateResponse('dashboard.html', context=context)
