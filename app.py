# app.py

import os
import json

from flask import Flask, request
import requests

app = Flask(__name__)

# Забираем из переменных окружения API-ключ и "имя приложения"/номер
GUPSHUP_API_KEY  = os.environ.get("GUPSHUP_API_KEY", "")
GUPSHUP_APP_NAME = os.environ.get("GUPSHUP_APP_NAME", "")  # обычно ваш WhatsApp-номер без "+"
GUPSHUP_SEND_URL = "https://api.gupshup.io/wa/api/v1/msg"

@app.route("/gupshup", methods=["POST"])
def gupshup_webhook():
    data = request.get_json(force=True)
    # inbound: в v2 это source, а не sender
    sender = data.get("source")
    text   = data.get("message", {}).get("text")

    app.logger.info("Webhook payload: %s", data)

    if not sender or not text:
        return ("", 400)

    # Формируем текст ответа
    reply = f"Вы написали: {text}"

    # Формируем form-data для Gupshup Send API
    payload = {
        "channel":     "whatsapp",
        "source":      GUPSHUP_APP_NAME,
        "destination": sender,
        "message":     json.dumps({"type":"text","text":reply})
    }
    headers = {
        "apikey":       GUPSHUP_API_KEY,
        "Content-Type": "application/x-www-form-urlencoded"
    }

    # Посылаем
    resp = requests.post(GUPSHUP_SEND_URL, data=payload, headers=headers)
    app.logger.info("Send API responded %s: %s", resp.status_code, resp.text)
    try:
        resp.raise_for_status()
    except Exception as e:
        app.logger.error("Ошибка при отправке ответа: %s", e)

    return ("", 200)

if __name__ == "__main__":
    # Railway сам прокидывает PORT, иначе 8080
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
