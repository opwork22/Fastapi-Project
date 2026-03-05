from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from auth import authenticate_user, hash_password, verify_password, create_access_token
from database import get_db
from models import RegisterRequest, NoteRequest, UpdateNoteRequest, UpdatePasswordRequest, DeleteRequest, User, Note

router = APIRouter()


@router.post("/register")
def register(user: RegisterRequest, db: Session = Depends(get_db)):

    existing = db.query(User).filter(User.username == user.username).first()

    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")

    hashed = hash_password(user.password)
    token = create_access_token(user.username)

    new_user = User(
        username=user.username,
        password=hashed,
        token=token
    )

    db.add(new_user)
    db.commit()

    return {"message": "User registered successfully"}


@router.get("/notes")
def get_notes(current=Depends(authenticate_user)):

    notes = [note.content for note in current.notes]

    return {"notes": notes}


@router.post("/notes/add")
def add_note(req: NoteRequest, db: Session = Depends(get_db), current=Depends(authenticate_user)):

    new_note = Note(content=req.note, user_id=current.id)

    db.add(new_note)
    db.commit()

    return {"message": "Note added successfully"}


@router.put("/update/note")
def update_note(req: UpdateNoteRequest, db: Session = Depends(get_db), current=Depends(authenticate_user)):

    notes = current.notes

    if req.note_index < 0 or req.note_index >= len(notes):
        raise HTTPException(status_code=400, detail="Invalid note index")

    note = notes[req.note_index]
    note.content = req.note

    db.commit()

    return {"message": "Note updated successfully"}


@router.put("/update/password")
def update_password(req: UpdatePasswordRequest, db: Session = Depends(get_db), current=Depends(authenticate_user)):

    if not verify_password(req.old_password, current.password):
        raise HTTPException(status_code=401, detail="Old password incorrect")

    current.password = hash_password(req.new_password)

    db.commit()

    return {"message": "Password updated successfully"}


@router.delete("/delete")
def delete(req: DeleteRequest, db: Session = Depends(get_db), current=Depends(authenticate_user)):

    if req.delete_type == "notes":

        if req.note_index is not None:

            notes = current.notes

            if req.note_index < 0 or req.note_index >= len(notes):
                raise HTTPException(status_code=400, detail="Invalid note index")

            db.delete(notes[req.note_index])

        else:
            for note in current.notes:
                db.delete(note)

    elif req.delete_type == "user":
        db.delete(current)

    else:
        raise HTTPException(status_code=400, detail="Invalid delete type")

    db.commit()

    return {"message": "Deleted successfully"}