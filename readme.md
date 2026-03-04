# FastAPI User Notes Authentication API

A simple FastAPI project that implements user authentication and notes management using a JSON file as the database.  


## Features

- User registration with username and password validation
- Password hashing using Argon2
- Store user data in a JSON file
- Add notes for a user
- Get notes only if correct username and password are provided
- Update notes
- Update password
- Delete notes or delete the entire user
- Password required before deleting data
- Pydantic validation for username and password

## Password Rules

- Minimum **8 characters**
- Must contain **at least one number**
- Must contain **at least one symbol**
- Username **cannot be numeric only**

Example valid password:

```
xxxx@12345
```

## Project Structure

```
project/
│
├── main.py
├── data.json
├── requirements.txt
└── README.md
```

## Installation

### 1. Clone the repository

```bash
git clone <repo_url>
cd project
```

### 2. Create virtual environment

```bash
python -m venv venv
```

Activate it

```bash
source venv/bin/activate
```

Windows

```bash
venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r Projectfastapi.requirements.txt
```

## Running the API

Start the FastAPI server:

```bash
uvicorn Projectfastapi.main:app --reload
```

Server will run at:

```
http://127.0.0.1:8000
```

Swagger documentation:

```
http://127.0.0.1:8000/docs
```

## API Endpoints

### Register User

```
POST /register
```

Body

```json
{
  "username": "omp",
  "password": "om@12345"
}
```

---

### Add Note

```
POST /notes/add
```

Body

```json
{
  "username": "omp",
  "password": "om@12345",
  "note": "This is my note"
}
```

---

### Get Notes

```
GET /notes
```

Query parameters

```
username=omp
password=om@12345
```

---

### Update Note

```
PUT /update/note
```

Body

```json
{
  "username": "omp",
  "password": "om@12345",
  "note_index": 0,
  "note": "Updated note"
}
```

---

### Update Password

```
PUT /update/password
```

Body

```json
{
  "username": "omp",
  "old_password": "om@12345",
  "new_password": "new@12345"
}
```

---

### Delete Notes or User

```
DELETE /delete
```

Delete only notes:

```json
{
  "username": "omp",
  "password": "om@12345",
  "delete_type": "notes"
}
```

Delete entire user:

```json
{
  "username": "omp",
  "password": "om@12345",
  "delete_type": "user"
}
```

## Data Storage

All data is stored in **data.json** in this format:

```json
{
  "omp": {
    "password": "hashed_password",
    "notes": [
      "note1",
      "note2"
    ]
  }
}
```
## Testing
- Swagger UI (`/docs`)
- Postman


