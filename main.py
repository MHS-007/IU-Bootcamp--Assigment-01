from fastapi import FastAPI, HTTPException, Body
from models import Student
from typing import List, Dict, Any
import os
from dotenv import load_dotenv

# LangChain + Gemini imports
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import initialize_agent, Tool

load_dotenv()  # load .env file

# ------------------------------------------------------
# FastAPI app initialization
# ------------------------------------------------------
app = FastAPI()


# ------------------------------------------------------
# In-memory storage (data will vanish if you restart app)
# ------------------------------------------------------
students: List[Dict[str, Any]] = []  # list of students
next_id = 1  # auto-incrementing student ID


# ------------------------------------------------------
# WEEK-1 CRUD ENDPOINTS
# ------------------------------------------------------

# 1) Get all students
@app.get("/students")
def GetStudents():
    return students


# 2) Get a single student by ID
@app.get("/students/{student_id}")
def GetStudentsByID(student_id: int):
    for student in students:
        if student["id"] == student_id:
            return student
    # agar student list mein nahi mila
    raise HTTPException(status_code=404, detail="Student not found")


# 3) Add a new student
@app.post("/students")
def AddStudent(student: Student):
    global next_id

    # Email should be unique (no duplicates allowed)
    for s in students:
        if s["email"] == student.email:
            raise HTTPException(status_code=400, detail="Email already exists")

    # Add new student with auto ID
    new_student = student.dict()
    new_student["id"] = next_id
    students.append(new_student)
    next_id += 1  # increment ID for next student

    return {"message": "Student added successfully", "student": new_student}


# 4) Update a student
@app.put("/students/{student_id}")
def UpdateStudent(student_id: int, UpdatedStudent: Student):
    for student in students:
        if student["id"] == student_id:

            # check if new email is already used by another student
            if any(s["email"] == UpdatedStudent.email and s["id"] != student_id for s in students):
                raise HTTPException(status_code=400, detail="Email already exists")

            # update student info
            student.update(UpdatedStudent.dict())
            return {"message": "Student updated successfully", "student": student}

    # agar student nahi mila
    raise HTTPException(status_code=404, detail="Student not found")


# 5) Delete a student
@app.delete("/students/{student_id}")
def DeleteStudent(student_id: int):
    for student in students:
        if student["id"] == student_id:
            students.remove(student)
            return {"message": "Student deleted successfully"}
    raise HTTPException(status_code=404, detail="Student not found")


# ------------------------------------------------------
# TOOLS (Functions used by the Agent)
# ------------------------------------------------------

# Tool 1: Add user using natural language
def add_user(user_input: str):
    """
    Example input:
    "Sara Ali, 27, female, saraali@gmail.com"
    """
    global next_id
    try:
        # Split input into 4 parts: Name, Age, Gender, Email
        parts = [p.strip() for p in user_input.split(",")]
        if len(parts) != 4:
            return "Format must be: Name, Age, Gender, Email"

        name, age, gender, email = parts
        age = int(age)  # convert string age to number

        # validate gender
        if gender.lower() not in ["male", "female", "other"]:
            return f"Invalid gender '{gender}'. Allowed: male, female, other."

        # check email is unique
        if any(s["email"] == email for s in students):
            return f"Email {email} already exists."

        # create new student
        new_user = {"id": next_id, "name": name, "age": age, "gender": gender, "email": email}
        students.append(new_user)
        next_id += 1
        return f"Added {name} successfully."

    except Exception as e:
        return f"Error: {str(e)}"


# Tool 2: Update user fields
def update_user(update_input: str):
    """
    Handles prompts like:
    - "Update user 1 email to sara.ali@uni.edu"
    - "Update user 1 age to 28 and name to Sara A."
    """
    try:
        words = update_input.lower().split()

        # check 'user' keyword
        if "user" not in words:
            return "Format must include 'Update user <id> ...'"

        # extract ID (word after 'user')
        user_index = words.index("user")
        user_id = int(words[user_index + 1])

        # rest of the command after ID
        rest_of_command = update_input.split(str(user_id), 1)[1].strip()

        updates = {}
        allowed_fields = ["name", "age", "gender", "email"]

        # parse multiple updates separated by 'and'
        for part in rest_of_command.split("and"):
            part = part.strip()
            if " to " in part:
                field, value = part.split(" to ", 1)

                # clean field
                field = field.strip().lower()
                if field not in allowed_fields:
                    continue  # ignore invalid fields

                # clean value (remove trailing . , etc.)
                value = value.strip().rstrip(",;")

                if field == "age":
                    value = int(value)

                updates[field] = value

        # apply updates
        for student in students:
            if student["id"] == user_id:
                if "email" in updates:
                    if any(s["email"] == updates["email"] and s["id"] != user_id for s in students):
                        return f"Email {updates['email']} already exists."
                student.update(updates)
                return f"Updated user {user_id} successfully."

        return f"User {user_id} not found."

    except Exception as e:
        return f"Error: {str(e)}"



# Tool 3: Delete user
def delete_user(user_input):
    """
    Expects input like: 2
    """
    try:
        user_id = int(user_input) if not isinstance(user_input, int) else user_input
        for student in students:
            if student["id"] == user_id:
                students.remove(student)
                return f"Deleted user {user_id} successfully."
        return f"User {user_id} not found."
    except Exception as e:
        return f"Error: {str(e)}"


# Tool 4: Get user
def get_user(user_input):
    """
    Expects input like: 1
    """
    try:
        user_id = int(user_input) if not isinstance(user_input, int) else user_input
        for student in students:
            if student["id"] == user_id:
                return {"users": students}
        return {"error": f"User {user_id} not found."}
    except Exception as e:
        return {"error": str(e)}

# Tool 5: List all users
def list_users(_input: str = None):
    """
    Returns the full list of users.
    Agent may pass a string, so we accept an optional argument.
    """
    return {"users": students}



# ------------------------------------------------------
# AGENT SETUP (LangChain + Gemini)
# ------------------------------------------------------

# Gemini API key
API_KEY = os.getenv("GOOGLE_API_KEY")

# LLM model (Gemini 2.5 Flash)
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", google_api_key=API_KEY)

# Register tools
tools = [
    Tool(name="Add User", func=add_user, description="Add a new user. Args: Name, Age, Gender, Email."),
    Tool(name="Update User", func=update_user, description="Update user by ID. Args: user_id and fields like name, age, gender, email."),
    Tool(name="Delete User", func=delete_user, description="Delete user by ID."),
    Tool(name="Get User", func=get_user, description="Get a user by ID."),
    Tool(name="List Users", func=list_users, description="List all users."),
]

# Initialize agent
agent = initialize_agent(
    tools,
    llm,
    agent="zero-shot-react-description",  # agent type (decides tool automatically)
    verbose=False
)


# ------------------------------------------------------
# NEW ROUTE: Agent Command
# ------------------------------------------------------
@app.post("/agent/command")
def agent_command(body: Dict[str, str] = Body(...)):
    """
    Send a plain English instruction to the agent.
    Example: { "prompt": "Add user Sara Ali, 27, female, saraali@gmail.com" }
    """
    prompt = body.get("prompt")
    if not prompt:
        raise HTTPException(status_code=400, detail="Prompt is required")

    # send prompt to agent
    response = agent.run(prompt)
    return {"result": response}
