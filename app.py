# app.py
import os
import json
import requests
from flask import Flask, request

app = Flask(__name__)

# из переменных окружения
GUPSHUP_API_KEY = os.getenv("GUPSHUP_API_KEY", "")
GUPSHUP_APP_NAME = os.getenv("GUPSHUP_APP_NAME", "")

if not GUPSHUP_API_KEY or not GUPSHUP_APP_NAME:
    raise RuntimeError("Не задан GUPSHUP_API_KEY или GUPSHUP_APP_NAME")

@app.route("/gupshup", methods=["POST"])
def gupshup_webhook():
    payload = request.get_json(force=True)

    # Gupshup v2: тело лежит в payload["data"]
    data = payload.get("data", {})
    sender = data.get("sender")              # "whatsapp:+7702xxxxxxx"
    incoming = data.get("message", {}).get("text")

    if not sender or not incoming:
        app.logger.error("Не получили sender/text в webhook")
        return "", 400

    # выдираем чистый номер без префикса
    number = sender.split(":")[-1]

    # здесь ваша логика: например, эхо-бот
    reply_text = f"Вы написали: «{incoming}»"

    # сформировать form-data для CAPI
    form = {
        "channel":     "whatsapp",
        "source":      GUPSHUP_APP_NAME,
        "destination": number,
        "message":     json.dumps({
            "type": "text",
            "text": reply_text
        })
    }

    headers = {
        "apikey":        GUPSHUP_API_KEY,
        "Content-Type":  "application/x-www-form-urlencoded"
    }

    # шлём ответ
    resp = requests.post(
        "https://api.gupshup.io/wa/api/v1/msg",
        headers=headers,
        data=form
    )

    if not resp.ok:
        app.logger.error(f"Ошибка при отправке ответа: {resp.status_code} — {resp.text}")

    # Gupshup ждёт 200
    return "", 200

if __name__ == "__main__":
    # в продакшене запускается через WSGI, здесь — для локального теста
    app.run(host="0.0.0.0", port=8080)
