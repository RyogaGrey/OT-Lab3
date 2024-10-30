import requests
import json
import sys
import argparse
from dotenv import load_dotenv
import os

# Загрузка переменных из файла .env
load_dotenv('.venv/.env')

# Получение токена и версии API из окружения
TOKEN = os.getenv("SERV_VK_TOKEN")
API_VERSION = os.getenv("VK_API_VERSION")

def get_vk_data(user_id, token):
    data = {}

    # Получаем основную информацию о пользователе
    user_url = f"https://api.vk.com/method/users.get?user_ids={user_id}&fields=followers_count&access_token={token}&v={API_VERSION}"
    user_response = requests.get(user_url)
    response_data = user_response.json()

    # Проверка на наличие ошибок в ответе
    if "error" in response_data:
        error_msg = response_data["error"].get("error_msg", "Unknown error")
        error_code = response_data["error"].get("error_code", "Unknown code")
        print(f"Ошибка при получении данных пользователя: {error_msg} (Код ошибки: {error_code})")
        return None

    # Извлекаем данные о пользователе
    user_info = response_data.get("response", [{}])
    if not user_info or not isinstance(user_info, list):
        print("Не удалось получить данные о пользователе. Неверный формат ответа.")
        return None

    data['user_info'] = user_info[0]

    # Получаем список подписчиков
    followers_url = f"https://api.vk.com/method/users.getFollowers?user_id={user_id}&count=10&access_token={token}&v={API_VERSION}"
    followers_response = requests.get(followers_url)
    data['followers'] = followers_response.json().get("response", {}).get("items", [])

    # Получаем список подписок
    subscriptions_url = f"https://api.vk.com/method/users.getSubscriptions?user_id={user_id}&extended=1&access_token={token}&v={API_VERSION}"
    subscriptions_response = requests.get(subscriptions_url)
    subscriptions_data = subscriptions_response.json().get("response", {})
    data['subscriptions'] = subscriptions_data.get("items", [])

    return data

def save_to_json(data, filename):
    # Создаем папку /user, если её нет
    os.makedirs("user", exist_ok=True)
    filepath = os.path.join("user", filename)
    
    # Сохраняем данные в JSON
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

    print(f"Данные сохранены в файл {filepath}")

def main():
    parser = argparse.ArgumentParser(description="VK User Info Fetcher")
    parser.add_argument('--user_id', type=str, help="ID пользователя VK", required=True)
    parser.add_argument('--output', type=str, help="Путь для сохранения файла результата (по умолчанию формируется автоматически)")
    args = parser.parse_args()

    user_id = args.user_id
    # Формируем имя файла на основе user_id, если оно не указано
    output_file = args.output or f"output_{user_id}.json"

    # Проверка токена
    if not TOKEN:
        print("Пожалуйста, укажите VK_TOKEN в .env файле.")
        sys.exit(1)

    print(f"Получение данных для пользователя с ID {user_id}")
    vk_data = get_vk_data(user_id, TOKEN)
    
    if vk_data is None:
        print("Не удалось получить данные о пользователе. Завершение программы.")
        sys.exit(1)

    # Сохранение данных в JSON файл
    save_to_json(vk_data, output_file)

if __name__ == "__main__":
    main()
