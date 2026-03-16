### FastAPI Project wit postgresql 

Project Structure-

project/

main.py          → FastAPI application entry point
auth.py          → Authentication logic (JWT + password hashing)
database.py      → Database connection (PostgreSQL)
models.py        → SQLAlchemy tables + Pydantic schemas
notes.py         → API routes (register, notes CRUD)
test.py          → Unit tests


### Flow of the application:

Client (Postman / Frontend)
        │
        ▼
FastAPI Router (notes.py)
        │
Authentication (auth.py)
        │
Database Session (database.py)
        │
SQLAlchemy Models (models.py)
        │
PostgreSQL Database



