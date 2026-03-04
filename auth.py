import os
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from passlib.hash import argon2
import jwt
from datetime import datetime, timedelta

from database import load_data, save_data

SECRET_KEY = "your_super_secret_key_here"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

security = HTTPBasic()


def hash_password(password: str):
    return argon2.hash(password)


def verify_password(password: str, hashed: str):
    return argon2.verify(password, hashed)


def create_access_token(username: str):
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    payload = {
        "sub": username,
        "exp": expire
    }

    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("sub")

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")

    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


def authenticate_user(credentials: HTTPBasicCredentials = Depends(security)):

    username = credentials.username
    password = credentials.password

    data = load_data()
    user = data.get(username)

    if not user or not verify_password(password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    token = user.get("token")

    if not token:
        token = create_access_token(username)
        user["token"] = token
        data[username] = user
        save_data(data)

    return username, user