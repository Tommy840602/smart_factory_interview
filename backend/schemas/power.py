from pydantic import BaseModel

class PowerStatus(BaseModel):
    reserve_percent: float
    reserve_w: float
    indicator: str