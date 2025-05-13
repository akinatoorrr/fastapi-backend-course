import json
import os
import requests
from fastapi import FastAPI, Body
from dotenv import load_dotenv


app = FastAPI()

load_dotenv()


class TaskFileManager:
    github_api = (
        "https://api.github.com/gists/"
        "fedd8d87e748082ba834bd1db2829c8d"
    )

    gist_token = os.getenv("GIST_TOKEN")
    file_name = 'tasks.json'

    def load_tasks(self):
        headers = {"Authorization": f"token {self.gist_token}"}
        resp = requests.get(self.github_api, headers=headers)
        resp.raise_for_status()
        gist = resp.json()
        content = gist["files"][self.file_name]["content"]
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return []

    def save_tasks(self, tasks):
        payload = {
            "files": {
                self.file_name: {
                    "content": json.dumps(tasks, indent=4, ensure_ascii=False)
                }
            }
        }
        headers = {"Authorization": f"token {self.gist_token}"}
        resp = requests.patch(self.github_api, json=payload, headers=headers)
        resp.raise_for_status()


file_class = TaskFileManager()


@app.get('/tasks')
def get_tasks():
    '''Возвращает все имеющиеся задачи в виде списка словарей'''
    return file_class.load_tasks()


@app.post('/tasks')
def create_task(task: dict = Body(...)):
    '''Создаёт новую задачу, статус по умолчанию - New'''
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
    '''Обновляет название задачи и её статус по указанному в url id'''
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
    '''Удаляет задачу по указанному в url id'''
    tasks = file_class.load_tasks()
    for i, task in enumerate(tasks):
        if task['id'] == task_id:
            del tasks[i]
            file_class.save_tasks(tasks)
            return {'message': 'Таск удален'}
    return {'error': 'Таск с таким id не найден'}
