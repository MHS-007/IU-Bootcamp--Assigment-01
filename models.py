from pydantic import BaseModel

class Student(BaseModel):
    name: str
    age: int
    gender: str
    email: str