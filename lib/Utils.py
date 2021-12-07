import json
import os
import requests
from getpass import getpass
from bs4 import BeautifulSoup

def get_session_cookie():
    sesh = requests.session()
    ans = sesh.get('https://cv-gml.ru/login')
    soup = BeautifulSoup(ans.text, 'html.parser')
    csrf_token = soup.find(id='csrf_token')['value']
    ans = sesh.post('https://cv-gml.ru/login', 
                    data={'email':input('Введите почту: '), 
                        'password':getpass('Введите пароль: '), 
                        'csrf_token': csrf_token})

    if ans.status_code != 200 or 'Неправильный логин или пароль' in ans.text:
        print('Ошибка! Неправильный логин или пароль')
        exit(1)
    
    return sesh.cookies['session']

def get_headers():
    if os.path.exists('headers.json'):
        with open('headers.json', 'r') as cookie:
            headers = json.loads(cookie.read())
        session = requests.session()
        data = session.get('https://cv-gml.ru/course/2/task/1', headers=headers)
        data = data.content.decode('utf-8')
        try:
            data.index("<a href='/login'>Войти</a>")
            
            login_bool = input("Сессия устарела. Войти через терминал? [Y/n] ").lower()
            while login_bool not in ('', 'n', 'y'):
                login_bool = input('Войти через терминал? [Y/n] ')
            
            if login_bool == 'n':
                exit(0)
        except Exception as e:
            return headers
    else:
        login_bool = input('Файл headers.json не найден. Войти через терминал? [Y/n] ').lower()
        while login_bool not in ('', 'n', 'y'):
            login_bool = input('Войти через терминал? [Y/n] ')

        if login_bool == 'n':
            exit(0)

    headers = login()
    print()
    return headers

def login():
    with open('default_headers.json', 'r') as cookie:
        headers = json.loads(cookie.read())
    headers['Cookie'] = f'session={get_session_cookie()}'

    with open('headers.json', 'w') as cookie:
        cookie.write(json.dumps(headers, indent=4))
    
    return headers