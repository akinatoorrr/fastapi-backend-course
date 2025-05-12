from fastapi import FastAPI, Body

app = FastAPI()

task_list = []


@app.get("/tasks")
def get_tasks():
    return task_list


@app.post("/tasks")
def create_task(task: dict = Body(...)):
    new_id = len(task_list) + 1
    task_list.append((new_id, task["title"], task.get("status", "New")))
    return {"message": "Таск создан"}


@app.put("/tasks/{task_id}")
def update_task(task_id: int, data: dict = Body(...)):
    if 0 < task_id <= len(task_list):
        task_list[task_id - 1] = (
            task_id,
            data["title"],
            data["status"]
        )
        return {"message": "Таск обновлен"}
    return {"error": "Таск с таким id не найден"}


@app.delete("/tasks/{task_id}")
def delete_task(task_id: int):
    if 0 < task_id <= len(task_list):
        task_list.pop(task_id - 1)
        return {"message": "Таск удален"}
    return {"error": "Таск с таким id не найден"}
