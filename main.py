from starlette.templating import Jinja2Templates
from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from database import  *

app = FastAPI()
templates = Jinja2Templates(directory="templates")


@app.get("/")
async def login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@app.get("/log")
async def logs(request: Request, name: str, password: str):
    kash = log(name, password)
    if kash:
        return templates.TemplateResponse("index.html", {
            "request": request,
            "username": name
        })
    else:
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": "Неверное имя пользователя или пароль"
        })


@app.get("/register")
async def register(name: str, password: str):
    try:
        existing_user = get_user_name(name)
        if existing_user:
            return {"error": "Пользователь уже существует"}

        add_user(name, password)
        return RedirectResponse(url="/", status_code=303)
    except Exception as e:
        return {"error": str(e)}


@app.get("/reg")
async def reg(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})


@app.get("/users")
async def get_users():
    users = get_all_users()
    return {"users": [{"id": u.id, "name": u.title} for u in users]}