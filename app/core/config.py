from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    nextjs_frontend_url: str = "http://localhost:3000"
    allow_origins: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    api_prefix: str = "/api"
    ws_prefix: str = "/ws"
    simulation_update_interval: float = 1.0
    database_url: str = "sqlite:///./fire_spread.db"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

        @classmethod
        def parse_env_var(cls, field_name: str, raw_val: str):
            if field_name == "allow_origins":
                return [url.strip() for url in raw_val.split(",")]
            return cls.json_loads(raw_val)

settings = Settings()