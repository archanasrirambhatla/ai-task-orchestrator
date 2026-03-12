from fastapi import FastAPI
from models import TaskInput
from classifier import classify_tasks
from scheduler import schedule_personal
from resource_allocator import allocate
from fastapi.middleware.cors import CORSMiddleware

# 1️⃣ Create FastAPI app first
app = FastAPI()

# 2️⃣ Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],       # allow all domains for dev/"hackathon"
    allow_credentials=True,
    allow_methods=["*"],       # allow POST, GET, OPTIONS, etc.
    allow_headers=["*"],
)

# 3️⃣ Define your API endpoint
@app.post("/generate-plan")
def generate_plan(data: TaskInput):

    classified = classify_tasks(data.tasks)

    personal = [t for t in classified if t["type"] == "personal"]
    business = [t for t in classified if t["type"] == "business"]

    personal_schedule = schedule_personal(personal)
    business_plan = allocate(business)

    return {
        "personal_schedule": personal_schedule,
        "business_plan": business_plan
    }