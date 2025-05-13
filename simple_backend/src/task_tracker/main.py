import json
from fastapi import FastAPI, Body

app = FastAPI()


class TaskFileManager:
    file_name = 'tasks.json'

    def load_tasks(self):
        try:
            with open(self.file_name, 'r', encoding='utf-8') as file:
                return json.load(file)
        except FileNotFoundError:
            return []
        except json.JSONDecodeError:
            return []

    def save_tasks(self, tasks):
        with open(self.file_name, 'w', encoding='utf-8') as file:
            json.dump(tasks, file, indent=4, ensure_ascii=False)


file_class = TaskFileManager()


@app.get('/tasks')
def get_tasks():
    return file_class.load_tasks()


@app.post('/tasks')
def create_task(task: dict = Body(...)):
    tasks = file_class.load_tasks()
    new_id = max((task['id'] for task in tasks), default=0) + 1
    new_task = {
        'id': new_id,
        'title': task['title'],
        'status': task.get('status', 'New')
    }
    tasks.append(new_task)
    file_class.save_tasks(tasks)
    return {'message': 'Таск создан'}


@app.put('/tasks/{task_id}')
def update_task(task_id: int, data: dict = Body(...)):
    tasks = file_class.load_tasks()
    updated_task = {
        'id': task_id,
        'title': data['title'],
        'status': data['status']
    }
    for i, task in enumerate(tasks):
        if task['id'] == task_id:
            tasks[i] = updated_task
            file_class.save_tasks(tasks)
            return {'message': 'Таск обновлен'}
    return {'error': 'Таск с таким id не найден'}


@app.delete('/tasks/{task_id}')
def delete_task(task_id: int):
    tasks = file_class.load_tasks()
    for i, task in enumerate(tasks):
        if task['id'] == task_id:
            del tasks[i]
            file_class.save_tasks(tasks)
            return {'message': 'Таск удален'}
    return {'error': 'Таск с таким id не найден'}
