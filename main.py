import requests
import json
import sys
import argparse

# Укажите свой токен доступа VK API
TOKEN = 'YOUR_ACCESS_TOKEN'
API_VERSION = '5.199'

def get_vk_data(user_id, token):
    data = {}

    # Получаем основную информацию о пользователе
    user_url = f"https://api.vk.com/method/users.get?user_ids={user_id}&fields=followers_count&access_token={token}&v={API_VERSION}"
    user_response = requests.get(user_url)
    user_info = user_response.json().get("response", [{}])[0]
    data['user_info'] = user_info

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

def save_to_json(data, filename='output.json'):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def main():
    parser = argparse.ArgumentParser(description="VK User Info Fetcher")
    parser.add_argument('--user_id', type=str, help="ID пользователя VK", default='YOUR_USER_ID')
    parser.add_argument('--output', type=str, help="Путь для сохранения файла результата", default='output.json')
    args = parser.parse_args()

    user_id = args.user_id
    output_file = args.output
    token = TOKEN

    if not token:
        print("Пожалуйста, укажите TOKEN в коде.")
        sys.exit(1)

    print(f"Получаем данные для пользователя с ID: {user_id}")
    vk_data = get_vk_data(user_id, token)
    save_to_json(vk_data, output_file)
    print(f"Данные сохранены в файл {output_file}")

if __name__ == "__main__":
    main()
