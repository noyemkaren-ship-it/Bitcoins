import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.templating import Jinja2Templates
from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse, JSONResponse
from typing import Dict, Set
from datetime import datetime, timedelta
import asyncio
from database import *


logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s]: %(message)s')
logger = logging.getLogger(__name__)
app = FastAPI()
templates = Jinja2Templates(directory="templates")
TRUSTED_IP_PREFIXES = ["176.195.", "127."]
tipp = []

class SecurityManager:
    def __init__(self):
        self.banned_ips: Set[str] = set()
        self.attempts: Dict[str, list] = {}
        self.max_attempts = 3
        self.ban_duration = timedelta(hours=48)

    def is_ip_trusted(self, ip: str) -> bool:
        return any(ip.startswith(prefix) for prefix in TRUSTED_IP_PREFIXES)

    def add_attempt(self, ip: str, path: str):
        if ip not in self.attempts:
            self.attempts[ip] = []

        current_time = datetime.utcnow()
        attempt_data = {
            'time': current_time,
            'path': path,
            'user_agent': 'unknown'
        }
        self.attempts[ip].append(attempt_data)
        filtered_attempts = [
            att for att in self.attempts[ip]
            if att['time'] > current_time - timedelta(minutes=5)
        ]

        if len(filtered_attempts) >= self.max_attempts:
            self.ban_ip(ip, "Too many failed attempts")

    def ban_ip(self, ip: str, reason: str = "Unauthorized access"):
        self.banned_ips.add(ip)
        logger.warning(f"Banning IP {ip}. Reason: {reason}")
        asyncio.create_task(self.notify_telegram(ip, reason))

    def clear_old_attempts(self):
        now = datetime.utcnow()
        for ip, attempts in list(self.attempts.items()):
            self.attempts[ip] = [
                att for att in attempts
                if att['time'] > now - timedelta(minutes=5)
            ]

            if not self.attempts[ip]:
                del self.attempts[ip]

    def unban_expired_ips(self):
        now = datetime.utcnow()
        expired_bans = [ip for ip in self.banned_ips if ip in self.attempts and all(
            att['time'] + self.ban_duration <= now for att in self.attempts[ip])]
        for ip in expired_bans:
            self.banned_ips.remove(ip)
            logger.info(f"Unbanned IP {ip}, ban duration has passed.")


class IPProtectionMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, security_manager: SecurityManager):
        super().__init__(app)
        self.security = security_manager

    async def dispatch(self, request: Request, call_next):
        client_ip = self.get_real_ip(request)
        if client_ip in self.security.banned_ips:
            return JSONResponse(
                status_code=403,
                content={"detail": "Access denied due to previous violations"}
            )

        self.security.add_attempt(client_ip, request.url.path)

        try:
            response = await call_next(request)
        except Exception as e:
            logger.error(f"Error processing request: {e}")
            response = JSONResponse(
                status_code=500,
                content={"detail": "Internal server error"}
            )

        return response

    @staticmethod
    def get_real_ip(request: Request) -> str:

        headers = request.headers
        xff = headers.get("X-Forwarded-For")
        if xff:
            ips = xff.split(",")
            last_ip = ips[-1].strip()
            return last_ip
        elif "X-Real-IP" in headers:
            return headers["X-Real-IP"]
        else:
            return request.client.host


class SecureHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["Content-Security-Policy"] = (
            "default-src 'none'; "
            "script-src 'self'; "
            "style-src 'self'; "
            "img-src 'self'; "
            "font-src 'self'; "
            "connect-src 'self';"
        )
        return response


security_manager = SecurityManager()
app.add_middleware(SecureHeadersMiddleware)
app.add_middleware(IPProtectionMiddleware, security_manager=security_manager)

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
