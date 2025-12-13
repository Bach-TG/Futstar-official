from pydantic import BaseModel


class RedisConfig(BaseModel):
    host: str
    port: str | int