async function generate() {

let tasksText = document.getElementById("tasks").value

let tasks = tasksText.split("\n")

let response = await fetch("http://127.0.0.1:8000/generate-plan", {

method: "POST",

headers: {
"Content-Type": "application/json"
},

body: JSON.stringify({
tasks: tasks
})

})

let data = await response.json()

document.getElementById("personal").innerText =
JSON.stringify(data.personal_schedule, null, 2)

document.getElementById("business").innerText =
JSON.stringify(data.business_plan, null, 2)

}