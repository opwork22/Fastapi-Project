import os
from fastapi import APIRouter, HTTPException, Depends

from auth import authenticate_user, hash_password, verify_password, create_access_token
from database import load_data, save_data
from models import RegisterRequest, NoteRequest, UpdateNoteRequest, UpdatePasswordRequest, DeleteRequest

router = APIRouter()


@router.post("/register")
def register(user: RegisterRequest):

    data = load_data()

    if user.username in data:
        raise HTTPException(status_code=400, detail="Username already exists")

    hashed = hash_password(user.password)
    token = create_access_token(user.username)

    data[user.username] = {
        "password": hashed,
        "notes": [],
        "token": token
    }

    save_data(data)

    return {"message": "User registered successfully"}


@router.get("/notes")
def get_notes(current=Depends(authenticate_user)):

    username, user_data = current

    return {
        "notes": user_data["notes"]
    }


@router.post("/notes/add")
def add_note(req: NoteRequest, current=Depends(authenticate_user)):

    username, user_data = current

    user_data["notes"].append(req.note)

    data = load_data()
    data[username] = user_data

    save_data(data)

    return {"message": "Note added successfully"}


@router.put("/update/note")
def update_note(req: UpdateNoteRequest, current=Depends(authenticate_user)):

    username, user_data = current

    if req.note_index < 0 or req.note_index >= len(user_data["notes"]):
        raise HTTPException(status_code=400, detail="Invalid note index")

    user_data["notes"][req.note_index] = req.note

    data = load_data()
    data[username] = user_data

    save_data(data)

    return {"message": "Note updated successfully"}


@router.put("/update/password")
def update_password(req: UpdatePasswordRequest, current=Depends(authenticate_user)):

    username, user_data = current

    if not verify_password(req.old_password, user_data["password"]):
        raise HTTPException(status_code=401, detail="Old password incorrect")

    user_data["password"] = hash_password(req.new_password)

    data = load_data()
    data[username] = user_data

    save_data(data)

    return {"message": "Password updated successfully"}


@router.delete("/delete")
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
        raise HTTPException(status_code=400, detail="Invalid delete type")

    save_data(data)

    return {"message": "Deleted successfully"}