import requests
import json
import sys
import argparse
import logging
from neo4j import GraphDatabase
from dotenv import load_dotenv
import os

# Загрузка переменных из .env файла
load_dotenv()

# Настройки VK API и Neo4j
TOKEN = os.getenv("VK_TOKEN")
API_VERSION = os.getenv("VK_API_VERSION", "5.131")
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

class VKDataFetcher:
    def __init__(self, user_id, depth=2):
        self.user_id = user_id
        self.depth = depth

    def fetch_user_data(self, user_id):
        url = f"https://api.vk.com/method/users.get?user_ids={user_id}&fields=sex,home_town,city,followers_count&access_token={TOKEN}&v={API_VERSION}"
        response = requests.get(url).json()
        user_data = response.get("response", [{}])[0]
        return {
            "id": user_data.get("id"),
            "screen_name": user_data.get("screen_name", ""),
            "name": f"{user_data.get('first_name', '')} {user_data.get('last_name', '')}",
            "sex": user_data.get("sex"),
            "city": user_data.get("city", {}).get("title", ""),
        }

    def fetch_followers(self, user_id):
        url = f"https://api.vk.com/method/users.getFollowers?user_id={user_id}&count=10&access_token={TOKEN}&v={API_VERSION}"
        response = requests.get(url).json()
        return response.get("response", {}).get("items", [])

    def fetch_subscriptions(self, user_id):
        url = f"https://api.vk.com/method/users.getSubscriptions?user_id={user_id}&extended=1&access_token={TOKEN}&v={API_VERSION}"
        response = requests.get(url).json()
        return response.get("response", {}).get("items", [])

    def fetch_data_recursive(self, user_id, depth):
        if depth == 0:
            return []

        logger.info(f"Fetching data for user {user_id} at depth {depth}")
        user_data = self.fetch_user_data(user_id)
        followers = self.fetch_followers(user_id)
        subscriptions = self.fetch_subscriptions(user_id)

        # Сохраняем данные о пользователе, фоллоуерах и подписках в Neo4j
        db.insert_user(user_data)
        for follower in followers:
            follower_data = self.fetch_user_data(follower)
            db.insert_user(follower_data)
            db.create_relationship(user_data['id'], follower, "Follow")
            self.fetch_data_recursive(follower, depth - 1)

        for subscription in subscriptions:
            if "type" in subscription and subscription["type"] == "page":
                db.insert_group(subscription)
                db.create_relationship(user_data['id'], subscription['id'], "Subscribe")
            elif "id" in subscription:
                subscription_data = self.fetch_user_data(subscription['id'])
                db.insert_user(subscription_data)
                db.create_relationship(user_data['id'], subscription['id'], "Follow")
                self.fetch_data_recursive(subscription['id'], depth - 1)

class Neo4jDB:
    def __init__(self):
        self.driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

    def close(self):
        self.driver.close()

    def insert_user(self, user_data):
        with self.driver.session() as session:
            session.run(
                "MERGE (u:User {id: $id}) SET u.screen_name = $screen_name, u.name = $name, u.sex = $sex, u.city = $city",
                user_data
            )

    def insert_group(self, group_data):
        with self.driver.session() as session:
            session.run(
                "MERGE (g:Group {id: $id}) SET g.name = $name, g.screen_name = $screen_name",
                {"id": group_data["id"], "name": group_data["name"], "screen_name": group_data.get("screen_name", "")}
            )

    def create_relationship(self, user_id, target_id, relationship_type):
        with self.driver.session() as session:
            session.run(
                f"MATCH (u:User {{id: $user_id}}), (t {{id: $target_id}}) "
                f"MERGE (u)-[:{relationship_type}]->(t)",
                {"user_id": user_id, "target_id": target_id}
            )

    def run_query(self, query):
        with self.driver.session() as session:
            result = session.run(query)
            return [record for record in result]

# Запросы для выборки данных
queries = {
    "total_users": "MATCH (u:User) RETURN count(u) AS total_users",
    "total_groups": "MATCH (g:Group) RETURN count(g) AS total_groups",
    "top_5_users": "MATCH (u:User)<-[:Follow]-() RETURN u.name, count(*) AS followers ORDER BY followers DESC LIMIT 5",
    "top_5_groups": "MATCH (g:Group)<-[:Subscribe]-() RETURN g.name, count(*) AS followers ORDER BY followers DESC LIMIT 5",
    "mutual_followers": """
        MATCH (u1:User)-[:Follow]->(u2:User), (u2)-[:Follow]->(u1)
        RETURN u1.name AS user1, u2.name AS user2
    """
}

def main():
    parser = argparse.ArgumentParser(description="VK Data Fetcher with Neo4j Integration")
    parser.add_argument('--user_id', type=str, help="ID пользователя VK для сбора данных", required=True)
    parser.add_argument('--depth', type=int, help="Глубина сбора данных", default=2)
    parser.add_argument('--query', type=str, help="Тип запроса для выполнения", choices=queries.keys())
    args = parser.parse_args()

    global db
    db = Neo4jDB()
    vk_fetcher = VKDataFetcher(args.user_id, args.depth)

    try:
        if args.query:
            # Выполнить запрос, если указан
            results = db.run_query(queries[args.query])
            for result in results:
                print(result)
        else:
            # Собрать данные на указанную глубину
            vk_fetcher.fetch_data_recursive(args.user_id, args.depth)
    except Exception as e:
        logger.error(f"Произошла ошибка: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    main()
