from typing import Optional
from fastapi import FastAPI, Form, Depends
from fastapi.security import OAuth2PasswordBearer

app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


@app.get('/')
def root():
    return {}


@app.post('/login/')
async def login(username: str = Form(...), password: str = Form(...)):
    user_dict = fake_users_db.get(form_data.username)
    if not user_dict:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    user = UserInDB(**user_dict)
    hashed_password = fake_hash_password(form_data.password)
    if not hashed_password == user.hashed_password:
        raise HTTPException(status_code=400, detail="Incorrect username or password")

    return {"access_token": user.username, "token_type": "bearer"}

    return {'username': username, 'password': password}


@app.get("/items/")
async def read_items(token: str = Depends(oauth2_scheme)):
    return {"token": token}

@app.get('/users')
def list_user():
    return {}


@app.get('/courses')
async def courses():
    return {}

@app.get('/users/{uid}')
def get_user(uid: int):
    return {}


@app.get('/users/{uid}/courses')
def get_user_courses(uid: int):
    return {}


@app.get('/user/{uid}/courses/{cid}')
def get_user_course(uid: int, cid: int):
    return {}
