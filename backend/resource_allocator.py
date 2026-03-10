team = [

 {"name":"Alex","skills":["marketing"]},
 {"name":"Sam","skills":["devops"]},
 {"name":"Lisa","skills":["sales"]}

]

def allocate(tasks):

    assignments = []

    for i, task in enumerate(tasks):

        member = team[i % len(team)]

        assignments.append({
            "task": task["name"],
            "assigned_to": member["name"]
        })

    return assignments