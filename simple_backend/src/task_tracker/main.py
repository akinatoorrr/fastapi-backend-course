import json
import os
import requests
from abc import ABC, abstractmethod
from fastapi import FastAPI, Body
from dotenv import load_dotenv


app = FastAPI()

load_dotenv()


class BaseHTTPClient(ABC):
    '''Абстрактный класс для HTTP запросов'''
    def __init__(self, token_env_var):
        self.token = os.getenv(token_env_var)
        if not self.token:
            raise ValueError(f'Не установлен {token_env_var} токен.')
        self.headers = self._build_headers()

    @abstractmethod
    def _build_headers(self):
        pass

    def get(self, url):
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()

    def post(self, url, json_payload):
        response = requests.post(url, headers=self.headers, json=json_payload)
        response.raise_for_status()
        return response.json()

    def patch(self, url, json_payload):
        response = requests.patch(url, headers=self.headers, json=json_payload)
        response.raise_for_status()
        return response.json()


class LLMManager(BaseHTTPClient):
    '''Класс-наследник для работы с LLM'''
    def __init__(self):
        super().__init__('AI_API_TOKEN')
        self.api_base_url = (
            'https://api.cloudflare.com/client/v4/accounts/'
            '20899bfe61320c4b5b2765c3cb8ed8be/ai/run/'
        )
        self.model = '@cf/meta/llama-3-8b-instruct'

    def _build_headers(self):
        return {'Authorization': f'Bearer {self.token}'}

    def run_model(self, task):
        payload = {'prompt': f'How to solve this task: {task}'}
        url = f'{self.api_base_url}{self.model}'
        response = self.post(url, payload)
        return response['result']['response']


class TaskFileManager(BaseHTTPClient):
    '''Класс-наследник для работы с Github Gist'''
    def __init__(self):
        super().__init__('GIST_TOKEN')
        self.github_api = (
            'https://api.github.com/gists/'
            'fedd8d87e748082ba834bd1db2829c8d'
        )
        self.file_name = 'tasks.json'

    def _build_headers(self):
        return {'Authorization': f'token {self.token}'}

    def load_tasks(self):
        gist = self.get(self.github_api)
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
        self.patch(self.github_api, payload)


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
