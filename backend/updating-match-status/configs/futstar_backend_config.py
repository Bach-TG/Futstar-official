from pydantic import BaseModel


class FutstarBackendConfig(BaseModel):
    host: str
    port: str | int