import os
import json
import requests
from flask import Flask, request

app = Flask(__name__)

# Конфигурация через переменные окружения
GUPSHUP_API_KEY  = os.environ.get("GUPSHUP_API_KEY", "")
GUPSHUP_APP_NAME = os.environ.get("GUPSHUP_APP_NAME", "")
# Endpoint для отправки через Gupshup Session API
GUPSHUP_SEND_URL  = "https://api.gupshup.io/sm/api/v1/msg"

# Загружаем каталог товаров
with open("products.json", encoding="utf-8") as f:
    catalog = json.load(f)

# Функция поиска товаров
def find_products(query, diameter, power):
    q = query.lower()
    candidates = [
        {**prod, "diff": abs(prod.get("power", 0) - power)}
        for prod in catalog
        if prod.get("diameter") == diameter and any(s in q for s in prod.get("synonyms", []))
    ]
    candidates.sort(key=lambda x: x["diff"])
    return candidates[:2]

# Функция отправки сообщения в Gupshup, всегда обрабатывает ошибки
def send_to_gupshup(dest, message_obj):
    payload = {
        "source":      GUPSHUP_APP_NAME,
        "destination": dest,
        "message":     message_obj
    }
    headers = {
        "Content-Type": "application/json",
        "apikey":       GUPSHUP_API_KEY
    }
    try:
        resp = requests.post(GUPSHUP_SEND_URL, json=payload, headers=headers)
        if resp.status_code != 200:
            app.logger.error(f"Gupshup send failed: {resp.status_code} - {resp.text}")
        else:
            app.logger.info(f"Gupshup send success: {resp.status_code}")
    except Exception as e:
        app.logger.error(f"Exception sending to Gupshup: {e}")

# Webhook для входящих сообщений от Gupshup
@app.route("/gupshup", methods=["POST"])
def gupshup_webhook():
    data = request.get_json(silent=True) or {}
    # Пропускаем все события, кроме входящих сообщений
    if "message" not in data:
        return "", 200

    sender = data.get("sender") or data.get("source")
    text   = data["message"].get("text", "").strip()
    parts  = text.split()

    # Ожидаем формат: товар диаметр мощность
    try:
        diameter = int(parts[-2])
        power    = int(parts[-1])
        query    = " ".join(parts[:-2])
    except (ValueError, IndexError):
        fallback = {"type": "text", "text": (
            "Пожалуйста, пришлите запрос в формате:\n"
            "товар диаметр мощность\n"
            "Пример: болгарка 125 1000"
        )}
        send_to_gupshup(sender, fallback)
        return "", 200

    matches = find_products(query, diameter, power)
    if not matches:
        send_to_gupshup(sender, {"type": "text", "text": "Ничего не найдено по вашим параметрам."})
        return "", 200

    # Отправляем найденные товары: картинка + текст
    for prod in matches:
        if img := prod.get("image_url"):
            send_to_gupshup(sender, {"type": "image", "url": img})
        msg        = (
            f"{prod['name']}\n"
            f"Диаметр: {prod['diameter']} мм\n"
            f"Мощность: {prod['power']} Вт\n"
            f"Цена для физ. лиц — смотрите в Kaspi:\n{prod['kaspi_link']}"
        )
        send_to_gupshup(sender, {"type": "text", "text": msg})

    return "", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
