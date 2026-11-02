import os
from pydantic import BaseModel

class Settings(BaseModel):
    PROJECT_NAME: str = "FilterTwin"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./filtertwin.db")
    CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:80",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "*"
    ]
    DEFAULT_RANDOM_SEED: int = 42
    ML_ARTIFACTS_DIR: str = os.path.join(os.path.dirname(os.path.dirname(__file__)), "ml_artifacts")

settings = Settings()
os.makedirs(settings.ML_ARTIFACTS_DIR, exist_ok=True)
