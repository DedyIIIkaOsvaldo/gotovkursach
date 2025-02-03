from typing import Union, List, Dict
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import json
import time
import os
import hashlib
import base64
import bcrypt

class User(BaseModel):
    login: str
    password: str
    role: str
    id: Union[int, None] = None
    token: Union[str, None] = None

class LogoutRequest(BaseModel):
    login: str

class LoginPassword(BaseModel):
    login: str
    password: str

class Update_array_client(BaseModel):
    position: str
    element: List[int]
    

class ChangePasswordRequest(BaseModel):
    login: str
    old_password: str
    new_password: str

class SortRequest(BaseModel):
    array: List[int]
    user_login: str


class TextData(BaseModel):
    text_id: Union[int, None] = None
    content: str


app = FastAPI()

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

def generate_token(user_id: int) -> str:
    return base64.urlsafe_b64encode(
        hashlib.sha256(f"{user_id}-{time.time()}".encode()).digest()
    ).decode()

def load_json(file_path: str):
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None

def save_json(file_path: str, data):
    with open(file_path, 'w') as f:
        json.dump(data, f)

# Регистрация пользователя
@app.post("/users")
def create_user(user: User):
    user.id = int(time.time())
    user.token = generate_token(user.id)
    user.password = hash_password(user.password) 

    print(f"Hashed password: {user.password}")

    folder_path = 'users/'
    os.makedirs(folder_path, exist_ok=True)

    for file in os.listdir(folder_path):
        if file.endswith('.json'):
            file_path = os.path.join(folder_path, file)
            existing_user = load_json(file_path)
            if existing_user and existing_user.get('login') == user.login:
                raise HTTPException(status_code=409, detail="User already exists")

    save_json(f"users/user_{user.id}.json", user.dict())
    return {"message": "User registered successfully", "token": user.token}

# Авторизация пользователя
@app.post("/users/login")
def login_user(data: LoginPassword):
    
    folder_path = 'users/'

    for file in os.listdir(folder_path):
     
        if file.endswith('.json'):
            file_path = os.path.join(folder_path, file)
            user = load_json(file_path)
        
            if user and user['login'] == data.login:
                stored_password = user['password']
                
                print(f"Stored hashed password: {stored_password}")
                print(f"Input password: {data.password}")

                if verify_password(data.password, stored_password):
                    return {"message": "Login successful", "token": user['token']}
    
    raise HTTPException(status_code=401, detail="Invalid login or password")

@app.post("/users/logout")
def logout_user(request_data: LogoutRequest):
    folder_path = 'users/'
    for file in os.listdir(folder_path):
        if file.endswith('.json'):
            file_path = os.path.join(folder_path, file)
            user = load_json(file_path)
            if user and user['login'] == request_data.login:
                user['token'] = None  # Удаляем токен
                save_json(file_path, user)
                return {"message": "Logout successful"}
    
    raise HTTPException(status_code=404, detail="User not found")

# Сортировка массива
@app.post("/sort")
def sort_array(sort_request: SortRequest):
    array = sort_request.array
    user_login = sort_request.user_login
    print(user_login)
    if not array:
        raise HTTPException(status_code=400, detail="Array cannot be empty")

    # Гномья сортировка
    def gnome_sort(arr):
        index = 0
        while index < len(arr):
            if index == 0:
                index += 1
            if arr[index] >= arr[index - 1]:
                index += 1
            else:
                arr[index], arr[index - 1] = arr[index - 1], arr[index]
                index -= 1
        return arr

    sorted_array = gnome_sort(array)
    history_file = f"history/{user_login}_history.json"
    
    # Добавление отсортированного массива в историю
    history = load_json(history_file) or []
    history.append(sorted_array)
    save_json(history_file, history)

    return {"sorted_array": sorted_array}

@app.get("/arrays/{user_login}")
def get_array_slice(user_login: str, start: int, end: int):
    history_file = f"history/{user_login}_history.json"
    history = load_json(history_file)
    if not history:
        raise HTTPException(status_code=404, detail="History not found")
    if start < 0 or end > len(history) or start >= end:
        raise HTTPException(status_code=400, detail="Invalid indices")
    return {"array_slice": history[start:end]}

@app.patch("/arrays/{user_login}")
def update_array(user_login: str, position: str, element: int, index: Union[int, None] = None):
    history_file = f"history/{user_login}_history.json"
    history = load_json(history_file)
    if not history:
        raise HTTPException(status_code=404, detail="History not found")

    # Последний массив в истории
    if not history:
        raise HTTPException(status_code=400, detail="No arrays in history to modify")
    
    array = history[-1]  # Последний массив в истории
    
    # Добавление элемента в массив
    if position == "start":
        array.insert(0, element)
    elif position == "end":
        array.append(element)
    elif position == "after":
        if index is None or index < 0 or index >= len(array):
            raise HTTPException(status_code=400, detail="Invalid index for insertion")
        array.insert(index + 1, element)
    else:
        raise HTTPException(status_code=400, detail="Invalid position")
    
    # Обновляем последний массив в истории
    history[-1] = array
    save_json(history_file, history)

    return {"updated_array": array}

# Получение истории сортировок
@app.get("/history/{user_login}")
def get_sort_history(user_login: str):
    history_file = f"history/{user_login}_history.json"
    history = load_json(history_file)
    if history:
        return {"history": history}
    raise HTTPException(status_code=404, detail="History not found")

@app.delete("/arrays/{user_login}")
def delete_array_by_index(user_login: str, index: int):
    history_file = f"history/{user_login}_history.json"
    history = load_json(history_file)
    if not history:
        raise HTTPException(status_code=404, detail="History not found")

    if index < 0 or index >= len(history):
        raise HTTPException(status_code=400, detail="Invalid index")

    deleted_array = history.pop(index)
    save_json(history_file, history)

    return {"message": "Array deleted successfully", "deleted_array": deleted_array}


@app.delete("/history/{user_login}")
def delete_history(user_login: str):
    history_file = f"history/{user_login}_history.json"
    
    if os.path.exists(history_file):
        os.remove(history_file)  # Удаляем файл истории
        return {"message": "History deleted successfully"}
    
    raise HTTPException(status_code=404, detail="History not found")

# Изменение пароля
@app.patch("/users/password")
def change_password(request_data: ChangePasswordRequest):
    folder_path = 'users/'
    for file in os.listdir(folder_path):
        if file.endswith('.json'):
            file_path = os.path.join(folder_path, file)
            user = load_json(file_path)
            if user and user['login'] == request_data.login:
                if verify_password(request_data.old_password, user['password']):
                    user['password'] = hash_password(request_data.new_password)
                    user['token'] = generate_token(user['id'])
                    save_json(file_path, user)
                    return {"message": "Password changed successfully", "new_token": user['token']}
    raise HTTPException(status_code=401, detail="Invalid login or password")
