from pydantic import BaseSettings

class Settings(BaseSettings):
    mongo_uri: str
    redis_host: str
    redis_port: int
    jwt_secret: str

    class Config:
        env_file = ".env"

settings = Settings()
