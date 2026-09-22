from typing import Optional

from pydantic import BaseModel


class ArtistOut(BaseModel):
    id: int
    profile_pic: Optional[str] = None

    class Config:
        from_attributes = True
