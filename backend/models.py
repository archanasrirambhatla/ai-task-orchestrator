from pydantic import BaseModel
from typing import List

class TaskInput(BaseModel):
    tasks: List[str]

class Task(BaseModel):
    name: str
    type: str
    duration: int
    priority: int