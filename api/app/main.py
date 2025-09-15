from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging, sys, orjson
from .config import settings
from .routers import chat, health, assistant

class ORJSONLogger(logging.Formatter):
    def format(self, record):
        payload = {
            "level": record.levelname,
            "msg": record.getMessage(),
            "name": record.name,
        }
        return orjson.dumps(payload).decode()

def setup_logging():
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(ORJSONLogger())
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(logging.INFO)

def create_app() -> FastAPI:
    setup_logging()
    app = FastAPI(title="Egg API", version="1.0.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router)
    app.include_router(chat.router)
    app.include_router(assistant.router)
    return app

app = create_app()


