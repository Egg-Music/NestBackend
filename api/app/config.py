from pydantic import BaseModel
import os

class Settings(BaseModel):
    # server
    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = int(os.getenv("PORT", "8000"))
    env: str = os.getenv("ENV", "dev")

    # cors
    cors_origins: list[str] = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(",")

    # auth (optional simple bearer/JWT passthrough)
    require_auth: bool = os.getenv("REQUIRE_AUTH", "false").lower() == "true"
    auth_audience: str | None = os.getenv("AUTH_AUDIENCE")
    auth_issuer: str | None = os.getenv("AUTH_ISSUER")

    # OpenAI
    openai_api_key: str | None = os.getenv("OPENAI_API_KEY")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    openai_timeout_s: int = int(os.getenv("OPENAI_TIMEOUT_S", "90"))

settings = Settings()

