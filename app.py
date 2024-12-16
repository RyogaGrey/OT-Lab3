import requests
import json
import sys
import argparse
from dotenv import load_dotenv
import os

# Загрузка переменных из файла .env
load_dotenv(".venv/.env")

# Получение токена и версии API из окружения
TOKEN = os.getenv("SERV_VK_TOKEN")
API_VERSION = os.getenv("VK_API_VERSION")

if not TOKEN:
    print("Ошибка: переменная окружения SERV_VK_TOKEN не найдена. Укажите её в файле .env.")
    sys.exit(1)


def vk_api_request(endpoint, params):
    params.update({"access_token": TOKEN, "v": API_VERSION})
    try:
        response = requests.get(f"https://api.vk.com/method/{endpoint}", params=params)
        response.raise_for_status()
        data = response.json()

        if "error" in data:
            error_msg = data["error"].get("error_msg", "Unknown error")
            error_code = data["error"].get("error_code", "Unknown code")
            print(f"Ошибка VK API: {error_msg} (Код ошибки: {error_code})")
            return None

        return data.get("response", {})
    except requests.RequestException as e:
        print(f"Ошибка при запросе {endpoint}: {e}")
        return None


def get_vk_data(user_id):
    data = {}

    # Основная информация о пользователе
    user_info = vk_api_request("users.get", {"user_ids": user_id, "fields": "followers_count"})
    if not user_info:
        return None

    data["user_info"] = user_info[0]

    # Подписчики
    followers = vk_api_request("users.getFollowers", {"user_id": user_id, "count": 10})
    data["followers"] = followers.get("items", []) if followers else []

    # Подписки
    subscriptions = vk_api_request("users.getSubscriptions", {"user_id": user_id, "extended": 1})
    data["subscriptions"] = subscriptions.get("items", []) if subscriptions else []

    return data


def save_to_json(data, filename):
    os.makedirs("user", exist_ok=True)
    filepath = os.path.join("user", filename)

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

    print(f"Данные сохранены в файл {filepath}")


def main():
    """
    Главная функция программы.
    """
    parser = argparse.ArgumentParser(description="VK User Info Fetcher")
    parser.add_argument("--user_id", type=str, help="ID пользователя VK")
    parser.add_argument("--output", type=str, help="Путь для сохранения файла результата (по умолчанию формируется автоматически)")
    
    # Если запущено без аргументов, выводим подсказку
    if len(sys.argv) == 1:
        parser.print_help()
        print("\nОшибка: необходимо указать параметры для запуска программы.")
        sys.exit(1)

    args = parser.parse_args()

    user_id = args.user_id
    if not user_id:
        print("Ошибка: параметр '--user_id' обязателен.")
        sys.exit(1)

    output_file = args.output or f"output_{user_id}.json"

    print(f"Получение данных для пользователя с ID {user_id}...")

    vk_data = get_vk_data(user_id)
    if not vk_data:
        print("Не удалось получить данные о пользователе. Завершение программы.")
        sys.exit(1)

    save_to_json(vk_data, output_file)


if __name__ == "__main__":
    main()
