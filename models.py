from pydantic import BaseModel, Field, field_validator
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from database import Base


# -------- SQLAlchemy Tables --------

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password = Column(String)
    token = Column(String)

    notes = relationship("Note", back_populates="owner", cascade="all, delete")


class Note(Base):
    __tablename__ = "notes"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(String)
    user_id = Column(Integer, ForeignKey("users.id"))

    owner = relationship("User", back_populates="notes")


# -------- Pydantic Schemas --------

class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3)
    password: str = Field(..., min_length=8)

    @field_validator("username")
    def username_not_numeric(cls, v):
        if v.isdigit():
            raise ValueError("Username cannot be numeric only")
        return v

    @field_validator("password")
    def password_strength(cls, v):
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain a number")

        symbols = "!@#$%^&*(),.?\":{}|<>"

        if not any(c in symbols for c in v):
            raise ValueError("Password must contain a symbol")

        return v


class NoteRequest(BaseModel):
    note: str


class UpdateNoteRequest(BaseModel):
    note_index: int
    note: str


class UpdatePasswordRequest(BaseModel):
    old_password: str
    new_password: str


class DeleteRequest(BaseModel):
    delete_type: str
    note_index: int | None = None