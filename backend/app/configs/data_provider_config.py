from pydantic import BaseModel


class DataProviderConfig(BaseModel):
    host: str
    port: str | int
    domain: str | None = None
    use: str = "ip"  # "ip" or "domain"