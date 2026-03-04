import os
import json
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, field_validator
from typing import Dict
from passlib.hash import argon2  

app = FastAPI(title="User & Notes App")

# Password Hashing
def hash_password(password: str) -> str:
    return argon2.hash(password)  # no need to truncate

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return argon2.verify(plain_password, hashed_password)

# JSON File 
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "data.json")

# Helpers
def load_data() -> Dict:
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r") as f:
        content = f.read().strip()
        if not content:
            return {}
        return json.loads(content)

def save_data(data: Dict):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

def authenticate_user(username: str, password: str, data: Dict):
    user = data.get(username)
    if not user or not verify_password(password, user["password"]):
        raise HTTPException(status_code=401, detail="Username or password is incorrect")
    return user

# Pydantic Models 
class UserBase(BaseModel):
    username: str = Field(..., min_length=3)

    @field_validator("username")
    def username_not_numeric(cls, v):
        if v.isdigit():
            raise ValueError("Username cannot be numeric only")
        return v

class UserAuth(UserBase):
    password: str = Field(..., min_length=8)

    @field_validator("password")
    def password_strength(cls, v):
        if not any(char.isdigit() for char in v):
            raise ValueError("Password must contain at least one number")
        symbols = "!@#$%^&*(),.?\":{}|<>"
        if not any(char in symbols for char in v):
            raise ValueError("Password must contain at least one symbol")
        return v

class NoteRequest(BaseModel):
    username: str
    password: str
    note: str

class UpdateNoteRequest(BaseModel):
    username: str
    password: str
    note_index: int
    note: str

class UpdatePasswordRequest(BaseModel):
    username: str
    old_password: str
    new_password: str

class DeleteRequest(BaseModel):
    username: str
    password: str
    delete_type: str  # 'notes' or 'user'

# Endpoints
@app.post("/register")
def register(user: UserAuth):
    data = load_data()
    if user.username in data:
        raise HTTPException(status_code=400, detail="Username already exists")
    hashed_pwd = hash_password(user.password)
    data[user.username] = {"password": hashed_pwd, "notes": []}
    save_data(data)
    return {"message": "User registered successfully"}

@app.post("/notes/add")
def add_note(req: NoteRequest):
    data = load_data()
    user = authenticate_user(req.username, req.password, data)
    user["notes"].append(req.note)
    save_data(data)
    return {"message": "Note added successfully"}

@app.get("/notes")
def get_notes(username: str, password: str):
    data = load_data()
    user = authenticate_user(username, password, data)
    return {"notes": user["notes"]}

@app.delete("/delete")
def delete(req: DeleteRequest):
    data = load_data()
    user = authenticate_user(req.username, req.password, data)
    if req.delete_type == "notes":
        user["notes"] = []
    elif req.delete_type == "user":
        del data[req.username]
    else:
        raise HTTPException(status_code=400, detail="Invalid delete_type. Use 'notes' or 'user'")
    save_data(data)
    return {"message": f"{req.delete_type.capitalize()} deleted successfully"}

@app.put("/update/password")
def update_password(req: UpdatePasswordRequest):
    data = load_data()
    user = authenticate_user(req.username, req.old_password, data)
    if len(req.new_password) < 8 or not any(char.isdigit() for char in req.new_password) or \
       not any(char in "!@#$%^&*(),.?\":{}|<>" for char in req.new_password):
        raise HTTPException(status_code=400, detail="Password must be 8+ chars, include number & symbol")
    user["password"] = hash_password(req.new_password)
    save_data(data)
    return {"message": "Password updated successfully"}

@app.put("/update/note")
def update_note(req: UpdateNoteRequest):
    data = load_data()
    user = authenticate_user(req.username, req.password, data)
    if req.note_index < 0 or req.note_index >= len(user["notes"]):
        raise HTTPException(status_code=400, detail="Invalid note index")
    user["notes"][req.note_index] = req.note
    save_data(data)
    return {"message": "Note updated successfully"}