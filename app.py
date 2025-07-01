import os
import json
import logging
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

GUPSHUP_API_KEY  = os.environ["GUPSHUP_API_KEY"]
GUPSHUP_APP_NAME = os.environ["GUPSHUP_APP_NAME"]  # точное имя вашего App

# URL для отправки in-session ответов
SEND_URL = "https://api.gupshup.io/wa/api/v1/msg"

@app.route("/gupshup", methods=["POST"])
def gupshup_webhook():
    data = request.get_json(force=True)
    sender = None
    text   = None

    # 1) Пробуем Gupshup v2
    if "sender" in data and "message" in data and "text" in data["message"]:
        sender = data["sender"]
        text   = data["message"]["text"]

    # 2) Пробуем Meta v3
    elif "entry" in data:
        try:
            changes = data["entry"][0]["changes"][0]["value"]
            msg     = changes["messages"][0]
            sender  = msg.get("from")
            if msg["type"] == "text":
                text = msg["text"]["body"]
        except Exception:
            pass

    if not sender or not text:
        app.logger.error("Не получили sender/text в webhook")
        return "Bad Request", 400

    app.logger.info(f"Incoming from {sender}: {text!r}")

    # Вот тут ваша логика анализа текста и поиска по products.json, например:
    # response_text = find_product_info(text)

    # Для примера просто эхо-ответ:
    response_text = f"Вы написали: {text}"

    # Отправляем in-session ответ
    payload = {
        "channel":     "whatsapp",
        "source":      sender,              # бот отвечает на тот же номер, откуда пришёл
        "destination": sender,
        "src.name":    GUPSHUP_APP_NAME,
        "message": json.dumps({
            "type": "text",
            "text": response_text
        })
    }
    headers = {
        "apikey":       GUPSHUP_API_KEY,
        "Content-Type": "application/x-www-form-urlencoded"
    }
    resp = requests.post(SEND_URL, headers=headers, data=payload)
    if resp.status_code != 200:
        app.logger.error(f"Ошибка отправки в Gupshup CAPI {resp.status_code}: {resp.text}")
    else:
        app.logger.info(f"Sent echo to {sender}")

    return jsonify({}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "8080")))
