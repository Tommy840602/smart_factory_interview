from pydantic import BaseModel

class Location(BaseModel):
    lon:float
    lat:float