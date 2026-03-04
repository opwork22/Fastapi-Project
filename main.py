import os
import json
from datetime import datetime, timedelta
from typing import Dict

from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field, field_validator
from passlib.hash import argon2
import jwt

# -------------------- CONFIG -------------------- #
SECRET_KEY = "your_super_secret_key_here"  # use env variable in production
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

app = FastAPI(title="User & Notes App with JWT Auth")
security = HTTPBearer()

# -------------------- PASSWORD HASHING -------------------- #
def hash_password(password: str) -> str:
    return argon2.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return argon2.verify(plain_password, hashed_password)

# -------------------- JSON FILE -------------------- #
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

# -------------------- JWT UTILITIES -------------------- #
def create_access_token(username: str) -> str:
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": username, "exp": expire.timestamp()}
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

    # Save token to user's record in JSON
    data = load_data()
    if username in data:
        data[username]["token"] = token
        save_data(data)
    return token

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if not username:
            raise HTTPException(status_code=401, detail="Invalid token")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    # Check token matches stored token
    data = load_data()
    user = data.get(username)
    if not user or user.get("token") != token:
        raise HTTPException(status_code=401, detail="Invalid token")
    return username

# -------------------- AUTHENTICATION -------------------- #
def authenticate_user(username: str, password: str, data: Dict):
    user = data.get(username)
    if not user or not verify_password(password, user["password"]):
        raise HTTPException(status_code=401, detail="Username or password is incorrect")
    return user

# -------------------- Pydantic Models -------------------- #
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

class UserLogin(BaseModel):
    username: str
    password: str

class NoteRequest(BaseModel):
    note: str

class UpdateNoteRequest(BaseModel):
    note_index: int
    note: str

class UpdatePasswordRequest(BaseModel):
    old_password: str
    new_password: str

class DeleteRequest(BaseModel):
    delete_type: str  # 'notes' or 'user'

# -------------------- ENDPOINTS -------------------- #

@app.post("/register")
def register(user: UserAuth):
    data = load_data()
    if user.username in data:
        raise HTTPException(status_code=400, detail="Username already exists")
    hashed_pwd = hash_password(user.password)
    data[user.username] = {"password": hashed_pwd, "notes": [], "token": None}
    save_data(data)
    return {"message": "User registered successfully"}

@app.post("/login")
def login(user: UserLogin):
    data = load_data()
    auth_user = authenticate_user(user.username, user.password, data)
    token = create_access_token(user.username)
    return {"access_token": token, "token_type": "bearer"}

@app.post("/notes/add")
def add_note(req: NoteRequest, username: str = Depends(verify_token)):
    data = load_data()
    user = data[username]
    user["notes"].append(req.note)
    save_data(data)
    return {"message": "Note added successfully"}

@app.get("/notes")
def get_notes(username: str = Depends(verify_token)):
    data = load_data()
    user = data[username]
    return {"notes": user["notes"]}

@app.delete("/delete")
def delete(req: DeleteRequest, username: str = Depends(verify_token)):
    data = load_data()
    user = data[username]
    if req.delete_type == "notes":
        user["notes"] = []
    elif req.delete_type == "user":
        del data[username]
    else:
        raise HTTPException(status_code=400, detail="Invalid delete_type. Use 'notes' or 'user'")
    save_data(data)
    return {"message": f"{req.delete_type.capitalize()} deleted successfully"}

@app.put("/update/password")
def update_password(req: UpdatePasswordRequest, username: str = Depends(verify_token)):
    data = load_data()
    user = data[username]
    if not verify_password(req.old_password, user["password"]):
        raise HTTPException(status_code=401, detail="Old password is incorrect")
    if len(req.new_password) < 8 or not any(char.isdigit() for char in req.new_password) or \
       not any(char in "!@#$%^&*(),.?\":{}|<>" for char in req.new_password):
        raise HTTPException(status_code=400, detail="Password must be 8+ chars, include number & symbol")
    user["password"] = hash_password(req.new_password)
    save_data(data)
    return {"message": "Password updated successfully"}

@app.put("/update/note")
def update_note(req: UpdateNoteRequest, username: str = Depends(verify_token)):
    data = load_data()
    user = data[username]
    if req.note_index < 0 or req.note_index >= len(user["notes"]):
        raise HTTPException(status_code=400, detail="Invalid note index")
    user["notes"][req.note_index] = req.note
    save_data(data)
    return {"message": "Note updated successfully"}