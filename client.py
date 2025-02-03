import os
import json
import re
import requests
import random 




def send_request(method, url, data=None, params=None):
    response = None
    if method == 'POST':
        response = requests.post(url, json=data)
    elif method == 'GET':
        response = requests.get(url, params=params)
    elif method == 'DELETE':
        response = requests.delete(url, params=params)
    elif method == 'PATCH':
        response = requests.patch(url, params=params, json=data)
    
    if response is None:
        raise ValueError(f"Unsupported HTTP method: {method}")
    
    try:
        return response.json()
    except ValueError:
        return response.text

def send_post(url, data):
    
    response = requests.post(url, json=data)  # Передаем данные в формате JSON
    try:
        return response.json()  # Преобразуем ответ в JSON
    except ValueError:
        return response.text  # Если не JSON, возвращаем как текст

def gnome_sort_client(user_login):
    print("Выберите способ создания массива:")
    print("1 - Ввести элементы вручную")
    print("2 - Сгенерировать случайный массив")
    choice = input("Ваш выбор: ")

    array = []
    if choice == '1':
        try:
            n = int(input("Введите количество элементов массива: "))
            print("Введите элементы массива:")
            array = [int(input(f"Элемент {i+1}: ")) for i in range(n)]
        except ValueError:
            print("Ошибка ввода! Используйте только целые числа.")
            return None
    elif choice == '2':
        try:
            n = int(input("Введите длину массива: "))
            min_val = int(input("Минимальное значение: "))
            max_val = int(input("Максимальное значение: "))
            array = [random.randint(min_val, max_val) for _ in range(n)]
            print(f"Сгенерирован массив: {array}")
        except ValueError:
            print("Ошибка ввода! Используйте только целые числа.")
            return None
    else:
        print("Неверный выбор")
        return None

    data = {"array": array, "user_login": user_login}
    result = send_post(f"http://localhost:8000/sort", data)

    if isinstance(result, dict) and "sorted_array" in result:
        return result['sorted_array']
    else:
        print("Ошибка сортировки:", result)
        return None

def auth():
    login = input("Введите логин\n")
    if login == "":
        print("Введите логин")
        return login
    password = input("Введите пароль\n")

    user_data = {
        "login": login,
        "password": password
    }

    result = send_post(f"http://localhost:8000/users/login", user_data)
    if "token" in result:
        return {"login": login, "token": result["token"]}
    else:
        print("Неверные данные для авторизации.")
        return None

def validate_password(password: str) -> bool:
    if len(password) < 10:
        print("Пароль должен быть длиннее 10 символов.")
        return False
    if not re.search(r'[a-z]', password):
        print("Пароль должен содержать хотя бы одну строчную букву.")
        return False
    if not re.search(r'[A-Z]', password):
        print("Пароль должен содержать хотя бы одну заглавную букву.")
        return False
    if not re.search(r'\d', password):
        print("Пароль должен содержать хотя бы одну цифру.")
        return False
    return True


def registration():
    login = input("Введите логин\n")
    if login == "":
        print("Введите логин")
        return login
    password = input("Пароль должен быть длиннее 10 символов.\nПароль должен содержать хотя бы одну строчную букву.\nПароль должен содержать хотя бы одну заглавную букву.\nПароль должен содержать хотя бы одну цифру.\nВведите пароль\n")
    password_confirm = input("Подтвердите пароль\n")
    role = input("Введите роль\n")

    if password != password_confirm:
        print("Пароли не совпадают!")
        return
    if not validate_password(password):
        return

    user_data = {
        "login": login,
        "password": password,
        "role": role
    }

    # Прямо передаем словарь в запрос, без использования json.dumps()
    result = send_post(f"http://127.0.0.1:8000/users", user_data)
    print(result)


def save_sorted_array(user_login, sorted_arr):
    # Папка для истории сортировок
    history_folder = 'history'
    if not os.path.exists(history_folder):  # Проверка на наличие папки, если нет - создаем
        os.makedirs(history_folder)

    # Файл для истории пользователя
    history_file = os.path.join(history_folder, f'{user_login}_history.json')
    
    # Если файл уже существует, загружаем историю, иначе создаем новый список
    if os.path.exists(history_file):
        with open(history_file, 'r') as f:
            history = json.load(f)
    else:
        history = []

    # Добавляем новый отсортированный массив в историю
    # history.append(sorted_arr)

    # Сохраняем обновленную историю в файл
    with open(history_file, 'w') as f:
        json.dump(history, f)

    print(f"Массив добавлен в историю пользователя {user_login}")


def view_history( user_login):
    if not  user_login:
        print("Ошибка: Логин пользователя не указан.")
        return
    url = f"http://localhost:8000/history/{user_login}"
    result = send_request('GET', url, {})
    print("Результат запроса:", result)
    if isinstance(result, dict) and "history" in result:
        history = result["history"]
        if history:
            print(f"История сортировок для пользователя {user_login}:")
            for i, arr in enumerate(history, 1):
                print(f"{i}: {arr}")
        else:
            print(f"История сортировок пуста для пользователя {user_login}.")
    else:
        print("Ошибка при получении истории сортировок.")


def create_array(user_login):
    try:
        sorted_arr = gnome_sort_client(user_login)  # Получаем отсортированный массив

        if sorted_arr:  # Если сортировка прошла успешно
            print(f"Отсортированный массив: {sorted_arr}")
            save_sorted_array(user_login, sorted_arr)  # Сохраняем отсортированный массив в историю
        else:
            print("Ошибка сортировки!")
    except ValueError:
        print("Ошибка ввода данных!")

def delete_array(user_login):
    try:
        index = int(input("Введите номер массива для удаления: ")) - 1
        url = f"http://127.0.0.1:8000/arrays/{user_login}"
        result = send_request('DELETE', url, params={"index": index})

        if isinstance(result, dict) and "deleted_array" in result:
            print(f"Массив успешно удалён: {result['deleted_array']}")
        else:
            print(f"Ошибка: {result}")
    except ValueError:
        print("Неверный ввод. Пожалуйста, введите номер массива.")

def delete_history(user_login):
    url = f"http://127.0.0.1:8000/history/{user_login}"
    result = send_request('DELETE', url, {})
    if isinstance(result, dict) and "message" in result:
        print(result["message"])
    else:
        print("Ошибка при удалении истории.")

def change_password_client(user_login):
    if not user_login:
        print("Ошибка: Логин пользователя не указан.")
        return

    old_password = input("Введите текущий пароль: ")
    new_password = input("Введите новый пароль: ")
    new_password_confirm = input("Подтвердите новый пароль: ")

    if new_password != new_password_confirm:
        print("Новый пароль и подтверждение не совпадают.")
        return

    if not validate_password(new_password):
        print("Новый пароль не соответствует требованиям безопасности.")
        return

    data = {
        "login": user_login,
        "old_password": old_password,
        "new_password": new_password
    }

    url = "http://localhost:8000/users/password"
    result = send_request('PATCH', url, data)

    if isinstance(result, dict) and "message" in result:
        print(result["message"])
        if "new_token" in result:
            print(f"Ваш новый токен: {result['new_token']}")
    else:
        print("Ошибка при смене пароля:", result)

def update_array_client(user_login):
    if not user_login:
        print("Ошибка: Логин пользователя не указан.")
        return

    print("Выберите позицию для вставки элемента:")
    print("1 - В начало")
    print("2 - В конец")
    print("3 - После определенного индекса")

    try:
        position_choice = int(input("Ваш выбор: "))
    except ValueError:
        print("Ошибка: Введите число от 1 до 3.")
        return

    if position_choice not in [1, 2, 3]:
        print("Ошибка: Неверный выбор. Введите 1, 2 или 3.")
        return

    position = ""
    index = None

    if position_choice == 3:
        try:
            index = int(input("Введите индекс после которого вставить элемент: "))
        except ValueError:
            print("Ошибка: Индекс должен быть целым числом.")
            return
        position = "after"
    elif position_choice == 1:
        position = "start"
    else:
        position = "end"

    try:
        element = int(input("Введите число для добавления: "))
    except ValueError:
        print("Ошибка: Введите целое число.")
        return

    # Формируем query-параметры
    params = {
        "position": position,
        "element": element
    }
    if index is not None:
        params["index"] = index

    url = f"http://127.0.0.1:8000/arrays/{user_login}"
    
    # Отправляем параметры в URL (params=params)
    result = send_request('PATCH', url, params=params)

    if isinstance(result, dict) and "updated_array" in result:
        print(f"Обновленный массив: {result['updated_array']}")
    else:
        print(f"Ошибка при обновлении массива: {result}")

def get_array_slice_client(user_login):
   
    try:
        # Запрашиваем у пользователя начальный и конечный индексы
        start = int(input("Введите начальный индекс: "))
        end = int(input("Введите конечный индекс: "))

        # Формируем URL для запроса
        url = f"http://127.0.0.1:8000/arrays/{user_login}"
        
        # Параметры запроса (start и end передаются как query-параметры)
        params = {"start": start, "end": end}

        # Отправляем GET-запрос
        result = send_request('GET', url, params=params)

        # Обрабатываем ответ
        if isinstance(result, dict) and "array_slice" in result:
            print(f"Срез массива: {result['array_slice']}")
        else:
            print("Ошибка при получении массива:", result)
    except ValueError:
        print("Ошибка: Введите корректные числовые значения для индексов.")

def logout_client(user_login):
    url = "http://localhost:8000/users/logout"
    data = {"login": user_login}
    result = send_request('POST', url, data)
    if isinstance(result, dict) and "message" in result:
        print(result["message"])
    else:
        print("Ошибка при выходе из системы.")

# Основной цикл программы
while True:
    print("\nГлавное меню:")
    print("1 - Авторизация")
    print("2 - Регистрация")
    print("3 - Выход из программы")
    main_command = input("Введите номер команды: ")

    if main_command == "1":
        # Авторизация
        user = auth()
        if not user:
            continue

        # Цикл работы после успешной авторизации
        while True:
            print(f"\nДобро пожаловать, {user['login']}!")
            print("1 - Ввести массив для сортировки")
            print("2 - Просмотреть историю сортировок")
            print("3 - Удалить массив из истории")
            print("4 - Удалить всю историю")
            print("5 - Сменить пароль")
            print("6 - Изменить массив")
            print("7 - Получить срез массива")
            print("8 - Выйти из системы")

            user_command = input("Введите номер команды: ")

            if user_command == "1":
                create_array(user['login'])
            elif user_command == "2":
                view_history(user['login'])
            elif user_command == "3":
                delete_array(user['login'])
            elif user_command == "4":
                delete_history(user['login'])
            elif user_command == "5":
                change_password_client(user['login'])
            elif user_command == "6":
                update_array_client(user['login'])
            elif user_command == "7":
                get_array_slice_client(user['login'])
            elif user_command == "8":
                logout_client(user['login'])
                user = None
                break  # Выход в главное меню
            else:
                print("Неверная команда!")

    elif main_command == "2":
        # Регистрация
        registration()
    
    elif main_command == "3":
        print("Выход из программы...")
        break
    else:
        print("Неверная команда!")


