def classify_tasks(tasks):

    classified = []

    for task in tasks:

        text = task.lower()

        if any(word in text for word in ["gym","groceries","family","shopping","doctor"]):

            classified.append({
                "name": task,
                "type": "personal",
                "duration": 1,
                "priority": 2
            })

        else:

            classified.append({
                "name": task,
                "type": "business",
                "duration": 2,
                "priority": 3
            })

    return classified