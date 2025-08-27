# Student Management API

A simple Student Management API built with **FastAPI**.  
Supports adding, viewing, updating, and deleting student records using in-memory storage with Pydantic validation.

## 🚀 Features

- Add new students
- View all students
- View student by ID
- Update student details
- Delete student

## 📦 Requirements

- Python 3.8+
- FastAPI
- Uvicorn

Install dependencies:

```bash
pip install -r requirements.txt
```

## ▶️ Run the Server

```bash
uvicorn main:app --reload
```

Then open Swagger docs in your browser at:
👉 http://127.0.0.1:8000/docs

## 📌 Endpoints

- GET /students → Get all students
- GET /students/{id} → Get student by ID
- POST /students → Add new student
- PUT /students/{id} → Update student
- DELETE /students/{id} → Delete student

## 📝 Note

This project uses in-memory storage, so all student data will reset every time the server restarts.
