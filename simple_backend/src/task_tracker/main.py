import json
import os
import requests
from fastapi import FastAPI, Body
from dotenv import load_dotenv


app = FastAPI()

load_dotenv()


class LLMManager:
    '''Класс для решения задач с помощью LLM-модели'''
    ai_token = os.getenv('AI_API_TOKEN')
    API_BASE_URL = (
        'https://api.cloudflare.com/client/v4/accounts/'
        '20899bfe61320c4b5b2765c3cb8ed8be/ai/run/'
    )
    headers = {'Authorization': f'Bearer {ai_token}'}
    model = '@cf/meta/llama-3-8b-instruct'

    def run_model(self, task):
        payload = {'prompt': f'How to solve this task: {task}'}
        response = requests.post(
            f'{self.API_BASE_URL}{self.model}',
            headers=self.headers,
            json=payload
        )
        return response.json()['result']['response']


class TaskFileManager:
    '''Класс для stateless бэкэнда - храним данные на Github Gist'''
    github_api = (
        'https://api.github.com/gists/'
        'fedd8d87e748082ba834bd1db2829c8d'
    )

    gist_token = os.getenv('GIST_TOKEN')
    file_name = 'tasks.json'

    def load_tasks(self):
        headers = {'Authorization': f'token {self.gist_token}'}
        response = requests.get(self.github_api, headers=headers)
        response.raise_for_status()
        gist = response.json()
        content = gist['files'][self.file_name]['content']
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return []

    def save_tasks(self, tasks):
        payload = {
            'files': {
                self.file_name: {
                    'content': json.dumps(tasks, indent=4, ensure_ascii=False)
                }
            }
        }
        headers = {'Authorization': f'token {self.gist_token}'}
        response = requests.patch(
            self.github_api,
            json=payload,
            headers=headers
        )
        response.raise_for_status()


file_class = TaskFileManager()
ai_class = LLMManager()


@app.get('/tasks')
def get_tasks():
    '''Возвращает все имеющиеся задачи в виде списка словарей'''
    return file_class.load_tasks()


@app.post('/tasks')
def create_task(task: dict = Body(...)):
    '''Создаёт новую задачу, статус по умолчанию - New'''
    tasks = file_class.load_tasks()
    new_id = max((task['id'] for task in tasks), default=0) + 1
    solution = ai_class.run_model(task['title'])
    new_task = {
        'id': new_id,
        'title': task['title'] + ' Solution: ' + solution,
        'status': task.get('status', 'New')
    }
    tasks.append(new_task)
    file_class.save_tasks(tasks)
    return {'message': 'Таск создан'}


@app.put('/tasks/{task_id}')
def update_task(task_id: int, data: dict = Body(...)):
    '''Обновляет название задачи и её статус по указанному в url id'''
    tasks = file_class.load_tasks()
    solution = ai_class.run_model(data['title'])
    updated_task = {
        'id': task_id,
        'title': data['title'] + ' Solution: ' + solution,
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
