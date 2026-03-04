import os
import json
from datetime import datetime, timedelta
from typing import Dict

from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator
from passlib.hash import argon2
import jwt  # PyJWT

# Config
SECRET_KEY = "your_super_secret_key_here"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

app = FastAPI(title="User & Notes App with Swagger Login")

# -------------------- CORS -------------------- #
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # allow all origins
    allow_credentials=True,
    allow_methods=["*"],  # allow all HTTP methods
    allow_headers=["*"],  # allow all headers
)

security = HTTPBasic()

# Password Hashing
def hash_password(password: str) -> str:
    return argon2.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return argon2.verify(plain_password, hashed_password)

# JSON File
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "data.json")

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

# JWT Utils
def create_access_token(username: str) -> str:
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": username, "exp": expire}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def decode_access_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return username
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# Authentication
def authenticate_user(credentials: HTTPBasicCredentials = Depends(security)):
    username = credentials.username
    password = credentials.password

    data = load_data()
    user = data.get(username)

    if not user or not verify_password(password, user["password"]):
        raise HTTPException(status_code=401, detail="Username or password is incorrect")

    token = user.get("token")

    if not token:
        token = create_access_token(username)
        user["token"] = token
        data[username] = user
        save_data(data)
    else:
        try:
            decode_access_token(token)
        except HTTPException:
            token = create_access_token(username)
            user["token"] = token
            data[username] = user
            save_data(data)

    return username, user

# Pydantic Models
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
        if not any(char.isdigit() for char in v):
            raise ValueError("Password must contain at least one number")
        symbols = "!@#$%^&*(),.?\":{}|<>"
        if not any(char in symbols for char in v):
            raise ValueError("Password must contain at least one symbol")
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
    note_index: int = None

# Endpoints
@app.post("/register")
def register(user: RegisterRequest):
    data = load_data()

    if user.username in data:
        raise HTTPException(status_code=400, detail="Username already exists")

    hashed_pwd = hash_password(user.password)
    token = create_access_token(user.username)

    data[user.username] = {
        "password": hashed_pwd,
        "notes": [],
        "token": token
    }

    save_data(data)

    return {"message": "User registered successfully", "token": token}

@app.get("/notes")
def get_notes(current=Depends(authenticate_user)):
    username, user_data = current
    return {"notes": user_data["notes"], "token": user_data["token"]}

@app.post("/notes/add")
def add_note(req: NoteRequest, current=Depends(authenticate_user)):
    username, user_data = current

    user_data["notes"].append(req.note)

    data = load_data()
    data[username] = user_data
    save_data(data)

    return {"message": "Note added successfully", "token": user_data["token"]}

@app.put("/update/note")
def update_note(req: UpdateNoteRequest, current=Depends(authenticate_user)):
    username, user_data = current

    if req.note_index < 0 or req.note_index >= len(user_data["notes"]):
        raise HTTPException(status_code=400, detail="Invalid note index")

    user_data["notes"][req.note_index] = req.note

    data = load_data()
    data[username] = user_data
    save_data(data)

    return {"message": "Note updated successfully", "token": user_data["token"]}

@app.put("/update/password")
def update_password(req: UpdatePasswordRequest, current=Depends(authenticate_user)):
    username, user_data = current

    if not verify_password(req.old_password, user_data["password"]):
        raise HTTPException(status_code=401, detail="Old password is incorrect")

    if len(req.new_password) < 8 or not any(char.isdigit() for char in req.new_password) or \
       not any(char in "!@#$%^&*(),.?\":{}|<>" for char in req.new_password):
        raise HTTPException(status_code=400, detail="Password must be 8+ chars, include number & symbol")

    user_data["password"] = hash_password(req.new_password)

    data = load_data()
    data[username] = user_data
    save_data(data)

    return {"message": "Password updated successfully", "token": user_data["token"]}

@app.delete("/delete")
def delete(req: DeleteRequest, current=Depends(authenticate_user)):
    username, user_data = current

    data = load_data()

    if req.delete_type == "notes":

        if req.note_index is not None:

            if req.note_index < 0 or req.note_index >= len(user_data["notes"]):
                raise HTTPException(status_code=400, detail="Invalid note index")

            del user_data["notes"][req.note_index]

        else:
            user_data["notes"] = []

        data[username] = user_data

    elif req.delete_type == "user":

        del data[username]

    else:
        raise HTTPException(status_code=400, detail="Invalid delete_type. Use 'notes' or 'user'")

    save_data(data)

    return {
        "message": f"{req.delete_type.capitalize()} deleted successfully",
        "token": user_data.get("token")
    }