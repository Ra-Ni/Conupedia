import httpx
import uvicorn
from fastapi.encoders import jsonable_encoder

from app.dependencies import core
from app.main import app
from app.internals.globals import SERVER_IP, SERVER_PORT, TEMPLATES, SSC
from fastapi import Request


@app.get('/courses2')
async def get_course(request: Request, threshold: int = 50):
    async with httpx.AsyncClient() as client:
        query = """
           select ?id
           where {
           [] a schema:Course ;
               rdfs:label ?id ;
               schema:dateCreated ?date .
           } 
           order by desc(?date) 
           limit %s 
           """ % threshold
        response = await core.send(client, query, format='records')
        context = {'request': request,'items': response, 'title': 'Explore'}

        return TEMPLATES.TemplateResponse('course.html', context=context)

@app.get('/courses3')
async def get_course(request: Request, id: str):
    id = id.zfill(6)
    async with httpx.AsyncClient() as client:
        query = """
           select *
           where {
           ssc:%s a schema:Course ;
               rdfs:label ?id ;
               schema:courseCode ?code ;
               schema:name ?title ;
               schema:numberOfCredits ?credits ;
               schema:isPartOf ?degree ;
               schema:description ?description ;
               schema:dateCreated ?date .
           } 
           """ % id
        response = await core.send(client, query, format='dict')
        return jsonable_encoder(response)



if __name__ == '__main__':

    uvicorn.run(app, host=SERVER_IP, port=SERVER_PORT)