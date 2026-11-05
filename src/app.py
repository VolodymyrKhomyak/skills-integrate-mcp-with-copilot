"""
High School Management System API

A super simple FastAPI application that allows students to view and sign up
for extracurricular activities at Mergington High School.
"""

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
import os
from datetime import date
from pathlib import Path

app = FastAPI(title="Mergington High School API",
              description="API for viewing and signing up for extracurricular activities")

MAX_ACTIVITIES_PER_STUDENT = 2

# Mount the static files directory
current_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=os.path.join(Path(__file__).parent,
          "static")), name="static")

# In-memory activity database
activities = {
    "Chess Club": {
        "description": "Learn strategies and compete in chess tournaments",
        "schedule": "Fridays, 3:30 PM - 5:00 PM",
        "schedule_days": ["Friday"],
        "start_time": "15:30",
        "end_time": "17:00",
        "max_participants": 12,
        "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
    },
    "Programming Class": {
        "description": "Learn programming fundamentals and build software projects",
        "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
        "schedule_days": ["Tuesday", "Thursday"],
        "start_time": "15:30",
        "end_time": "16:30",
        "max_participants": 20,
        "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
    },
    "Gym Class": {
        "description": "Physical education and sports activities",
        "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
        "schedule_days": ["Monday", "Wednesday", "Friday"],
        "start_time": "14:00",
        "end_time": "15:00",
        "max_participants": 30,
        "participants": ["john@mergington.edu", "olivia@mergington.edu"]
    },
    "Soccer Team": {
        "description": "Join the school soccer team and compete in matches",
        "schedule": "Tuesdays and Thursdays, 4:00 PM - 5:30 PM",
        "schedule_days": ["Tuesday", "Thursday"],
        "start_time": "16:00",
        "end_time": "17:30",
        "max_participants": 22,
        "participants": ["liam@mergington.edu", "noah@mergington.edu"]
    },
    "Basketball Team": {
        "description": "Practice and play basketball with the school team",
        "schedule": "Wednesdays and Fridays, 3:30 PM - 5:00 PM",
        "schedule_days": ["Wednesday", "Friday"],
        "start_time": "15:30",
        "end_time": "17:00",
        "max_participants": 15,
        "participants": ["ava@mergington.edu", "mia@mergington.edu"]
    },
    "Art Club": {
        "description": "Explore your creativity through painting and drawing",
        "schedule": "Thursdays, 3:30 PM - 5:00 PM",
        "schedule_days": ["Thursday"],
        "start_time": "15:30",
        "end_time": "17:00",
        "max_participants": 15,
        "participants": ["amelia@mergington.edu", "harper@mergington.edu"]
    },
    "Drama Club": {
        "description": "Act, direct, and produce plays and performances",
        "schedule": "Mondays and Wednesdays, 4:00 PM - 5:30 PM",
        "schedule_days": ["Monday", "Wednesday"],
        "start_time": "16:00",
        "end_time": "17:30",
        "max_participants": 20,
        "participants": ["ella@mergington.edu", "scarlett@mergington.edu"]
    },
    "Math Club": {
        "description": "Solve challenging problems and participate in math competitions",
        "schedule": "Tuesdays, 3:30 PM - 4:30 PM",
        "schedule_days": ["Tuesday"],
        "start_time": "15:30",
        "end_time": "16:30",
        "max_participants": 10,
        "participants": ["james@mergington.edu", "benjamin@mergington.edu"]
    },
    "Debate Team": {
        "description": "Develop public speaking and argumentation skills",
        "schedule": "Fridays, 4:00 PM - 5:30 PM",
        "schedule_days": ["Friday"],
        "start_time": "16:00",
        "end_time": "17:30",
        "max_participants": 12,
        "participants": ["charlotte@mergington.edu", "henry@mergington.edu"]
    }
}


@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")


@app.get("/activities")
def get_activities():
    return activities


def _validate_registration_window(activity):
    today = date.today()
    try:
        registration_start = activity.get("registration_start")
        registration_end = activity.get("registration_end")
        if registration_start and date.fromisoformat(registration_start) > today:
            raise HTTPException(
                status_code=400,
                detail="Registration for this activity has not opened"
            )
        if registration_end and date.fromisoformat(registration_end) < today:
            raise HTTPException(
                status_code=400,
                detail="Registration for this activity has closed"
            )
    except ValueError as error:
        raise HTTPException(
            status_code=500,
            detail="Activity registration dates must use YYYY-MM-DD format"
        ) from error


def _has_schedule_conflict(activity, other_activity):
    shared_days = set(activity["schedule_days"]) & set(
        other_activity["schedule_days"]
    )
    return (
        bool(shared_days)
        and activity["start_time"] < other_activity["end_time"]
        and other_activity["start_time"] < activity["end_time"]
    )


@app.post("/activities/{activity_name}/signup")
def signup_for_activity(activity_name: str, email: str):
    """Sign up a student for an activity"""
    # Validate activity exists
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Get the specific activity
    activity = activities[activity_name]

    # Validate student is not already signed up
    if email in activity["participants"]:
        raise HTTPException(
            status_code=400,
            detail="Student is already signed up"
        )

    _validate_registration_window(activity)

    if len(activity["participants"]) >= activity["max_participants"]:
        raise HTTPException(status_code=400, detail="Activity is full")

    enrolled_activities = [
        (name, enrolled_activity)
        for name, enrolled_activity in activities.items()
        if email in enrolled_activity["participants"]
    ]
    if len(enrolled_activities) >= MAX_ACTIVITIES_PER_STUDENT:
        raise HTTPException(
            status_code=400,
            detail=(
                "Students may sign up for at most "
                f"{MAX_ACTIVITIES_PER_STUDENT} activities"
            )
        )

    for enrolled_name, enrolled_activity in enrolled_activities:
        if _has_schedule_conflict(activity, enrolled_activity):
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Schedule conflicts with the student's "
                    f"{enrolled_name} enrollment"
                )
            )

    # Add student
    activity["participants"].append(email)
    return {"message": f"Signed up {email} for {activity_name}"}


@app.delete("/activities/{activity_name}/unregister")
def unregister_from_activity(activity_name: str, email: str):
    """Unregister a student from an activity"""
    # Validate activity exists
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Get the specific activity
    activity = activities[activity_name]

    # Validate student is signed up
    if email not in activity["participants"]:
        raise HTTPException(
            status_code=400,
            detail="Student is not signed up for this activity"
        )

    # Remove student
    activity["participants"].remove(email)
    return {"message": f"Unregistered {email} from {activity_name}"}
