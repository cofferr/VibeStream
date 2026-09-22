from typing import Optional

from pydantic import BaseModel


class GenreBase(BaseModel):
    name: str
    description: Optional[str] = None


class GenreCreate(GenreBase):
    pass


class GenreUpdate(GenreBase):
    pass


class GenreOut(GenreBase):
    id: int

    class Config:
        from_attributes = True
