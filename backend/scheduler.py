from datetime import datetime, timedelta

def schedule_personal(tasks):

    start_time = datetime.strptime("06:00", "%H:%M")

    schedule = []

    for task in tasks:

        end_time = start_time + timedelta(hours=task["duration"])

        schedule.append({
            "task": task["name"],
            "start": start_time.strftime("%H:%M"),
            "end": end_time.strftime("%H:%M")
        })

        start_time = end_time

    return schedule