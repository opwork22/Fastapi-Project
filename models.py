import os
from pydantic import BaseModel, Field, field_validator


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