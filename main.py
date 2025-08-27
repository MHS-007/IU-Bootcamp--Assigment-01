from fastapi import FastAPI, HTTPException
from models import Student

app = FastAPI()

students = []
next_id = 1

@app.get("/students")
def GetStudents():
    return students


@app.get("/students/{student_id}")
def GetStudentsByID(student_id: int):
    for student in students:
        if student["id"] == student_id:
            return student
    raise HTTPException(status_code=404, detail="Student not found")


@app.post("/students")
def AddStudent(student: Student):
    global next_id
    new_student = student.dict()
    new_student["id"]= next_id
    students.append(new_student)
    next_id += 1
    return {"message" : "Student added successfully", "student": new_student}


@app.put("/students/{student_id}")
def UpdateStudent(student_id: int, UpdatedStudent: Student):
    for student in students:
        if student["id"] == student_id:
            student.update(UpdatedStudent.dict())
            return {"message" : "Student updated successfully", "student": student}
    raise HTTPException(status_code=404, detail="Student not found")


@app.delete("/students/{student_id}")
def DeleteStudent(student_id: int):
    for student in students:
        if student["id"] == student_id:
            students.remove(student)
            return {"message": "Student deleted successfully"}
    raise HTTPException(status_code=404, detail="Student not found")