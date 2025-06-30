import os
import json
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# --- Конфигурация через переменные окружения Railway ---
# Название вашего Gupshup-приложения
GUPSHUP_APP_NAME = os.environ.get("QwetAPItest")
# API-ключ Gupshup (см. Console → API keys)
GUPSHUP_API_KEY  = os.environ.get("sk_4e29a41731fd4ddbad63f0de680678aa")
# URL для отправки сообщений через Gupshup API
GUPSHUP_API_URL  = "https://api.gupshup.io/sm/api/v1/msg"

# Загружаем каталог товаров
with open("products.json", encoding="utf-8") as f:
    catalog = json.load(f)

# Ищем подходящие товары
def find_products(query, diameter, power):
    q = query.lower()
    candidates = [
        {**prod, "diff": abs(prod.get("power", 0) - power)}
        for prod in catalog
        if prod.get("diameter") == diameter and any(s in q for s in prod.get("synonyms", []))
    ]
    candidates.sort(key=lambda x: x["diff"])
    return candidates[:2]

# Функция отправки одного сообщения через Gupshup API
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
    resp = requests.post(GUPSHUP_API_URL, headers=headers, json=payload)
    return resp

# Webhook для входящих событий от Gupshup
@app.route("/gupshup", methods=["POST"])
def webhook():
    data = request.get_json(silent=True) or {}
    # Пропускаем все события, кроме входящего текстового сообщения
    if "message" not in data:
        return "", 200

    sender = data.get("sender")
    msg_text = data["message"].get("text", "").strip()
    parts = msg_text.split()

    # Ожидаем формат: "товар диаметр мощность"
    try:
        diam = int(parts[-2])
        powr = int(parts[-1])
        query = " ".join(parts[:-2])
    except (ValueError, IndexError):
        help_msg = {"type": "text", "text": (
            "Пожалуйста, в формате: товар диаметр мощность\n"
            "Пример: болгарка 125 1000"
        )}
        send_to_gupshup(sender, help_msg)
        return "", 200

    matches = find_products(query, diam, powr)
    if not matches:
        send_to_gupshup(sender, {"type":"text","text":"Ничего не найдено."})
        return "", 200

    # Отправляем найденные товары: картинка + текст
    for prod in matches:
        if prod.get("image_url"):
            send_to_gupshup(sender, {"type":"image", "url": prod["image_url"]})
        msg = (
            f"{prod['name']}\n"
            f"Диаметр: {prod['diameter']} мм\n"
            f"Мощность: {prod['power']} Вт\n"
            f"Цена для физ. лиц: {prod['kaspi_link']}"
        )
        send_to_gupshup(sender, {"type":"text", "text": msg})

    return "", 200

# Запуск
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
