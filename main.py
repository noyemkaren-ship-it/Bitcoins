from datetime import datetime
from starlette.templating import Jinja2Templates
from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from database import  *
from fastapi.responses import JSONResponse

app = FastAPI()
templates = Jinja2Templates(directory="templates")
tipp = []
ALLOWED_IPS = ["176.195.22.127", "127.0.0.1"]

@app.middleware("http")
async def ip_filter(request: Request, call_next):
    if request.client.host not in ALLOWED_IPS:
        print("КТО ТО СТАРАЛСЯ ЗАЙТИ В DOCS")
        print("Я ЕО ЗАБЛОКИРОВАЛ!")
        return JSONResponse(status_code=403, content={"error": "Access denied"})
    return await call_next(request)


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


@app.get("/oll/tap_up")
async def tp():
    return {
        "total": len(tipp),
        "transactions": tipp
    }


@app.get("/user/pl/balance")
async def top_up_balance(user_name: str, bl: int):
    try:
        user = get_user_name(user_name)

        if not user:
            return {
                "status": "error",
                "message": f"Пользователь '{user_name}' не найден"
            }, 404
        tipp.append({
            "name": user.title,
            "bl": bl,
            "user_id": user.id,
            "timestamp": str(datetime.now())  # добавляем время
        })
        print(f"✅ {user.title} (ID: {user.id}) подтверждает перевод на сумму {bl} RUB")
        print(f"📞 Реквизиты: +79040597343 Нагапетян (Альфа-Банк)")
        return {
            "status": "success",
            "message": f"Запрос на пополнение {bl} RUB для {user_name} получен",
            "user_id": user.id,
            "user_name": user.title,
            "current_balance": user.coins,
            "transaction_id": len(tipp) - 1
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {
            "status": "error",
            "message": f"Внутренняя ошибка сервера: {str(e)}"
        }, 500


@app.get("/bl")
async def bl(request: Request):
    return templates.TemplateResponse("bell.html", {"request": request})


@app.get("/ball")
async def bl(request: Request, name: str):
    user = get_user_name(name)
    if user:
        return templates.TemplateResponse("ball.html", {
            "request": request,
            "balance": user.coins,
            "name": name,
            "user_id": user.id
        })
    else:
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": f"Пользователь '{name}' не найден"
        })


@app.get("/update/balance")
async def update(id_user: int, balance: int):
    update_balance(id_user, balance)


@app.get("/user/{user_id}/name")
async def get_user_name_by_id(user_id: int):
    user = get_user(user_id)
    if user:
        return user.title
    else:
        return f"Пользователь с ID {user_id} не найден"
