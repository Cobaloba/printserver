from pydantic import BaseModel, Field


class NewRollRequest(BaseModel):
    width_mm: int = Field(gt=0)
    diameter_mm: int = Field(gt=0)
