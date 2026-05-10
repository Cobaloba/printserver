from pydantic import BaseModel


class NewRollRequest(BaseModel):
    width_mm: int
    diameter_mm: int
