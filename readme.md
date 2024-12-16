# VK User Info Fetcher

Программа для получения информации о пользователе ВКонтакте, его подписчиках и подписках через VK API. Результаты сохраняются в **читаемом формате JSON**.

---

## **Требования**

- **Python 3.10+**
- Аккаунт ВКонтакте с полученным токеном доступа (с правами `friends` и `groups`).
- Установленный `pip`.

---

## **Установка**

1. Cклонируйте репозиторий:
   ```bash
   git clone https://github.com/your-repo/vk-user-fetcher.git
   cd vk-user-fetcher
   ```
2. Создайте и заполните файл .env (.venv/.env) в корне проекта:

```
   SERV_VK_TOKEN=
   VK_API_VERSION=5.199
   NEO4J_URI=neo4j://localhost:7687
```
3. Установите зависимости

```
   pip install -r requirements.txt
```

## **Запуск**

```bash
python app.py --user_id <ID пользователя> (Опционально) --output <Путь и имя файла для вывода>.json
# Для справки используйте тег -h или --help
```