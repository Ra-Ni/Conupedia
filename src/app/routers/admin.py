from typing import Optional
import httpx
from fastapi import APIRouter, Request, Cookie, Response
from ..internals.globals import TEMPLATES
from ..dependencies import auth, core


router = APIRouter()


@router.get('/admin')
async def admin(request: Request, response: Response, token: Optional[str] = Cookie(None)):
    async with httpx.AsyncClient() as client:
        user = await auth.get_user(client, token, as_root=True)
        query = """
        select ?id ?course 
        where {
            [] a schema:Course ;
                rdfs:label ?id ;
                schema:courseCode ?code ;
                schema:name ?title .
            bind(concat(?code," - ",?title) as ?course)
        } 
        """

        response = await core.send(client, query, format='records')
        context = {'request': request, 'entries': response, 'user_info': user}
    return TEMPLATES.TemplateResponse('admin.html', context=context)

