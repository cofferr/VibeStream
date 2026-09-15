from pydantic import BaseModel
from typing import Optional


class ArtistOut(BaseModel):
    id: int
    profile_pic: Optional[str] = None

    class Config:
        from_attributes = True
