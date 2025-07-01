import os
from flask import Flask, request
import requests

app = Flask(__name__)

# Окружение (Railway Variables):
# GUPSHUP_API_KEY — ваш API-ключ (sk_…)
# GUPSHUP_SOURCE_NUMBER — ваш WhatsApp-номер без '+' (например, '77021682964')
GUPSHUP_API_KEY       = os.environ["GUPSHUP_API_KEY"]
GUPSHUP_SOURCE_NUMBER = os.environ["GUPSHUP_SOURCE_NUMBER"]

@app.route("/gupshup", methods=["POST"])
def gupshup_webhook():
    # Принимаем данные от Gupshup
    data = request.get_json(force=True) or {}
    sender = data.get("sender") or data.get("from")
    text   = data.get("message", {}).get("text", "").strip()

    # Логируем входящее сообщение
    app.logger.info("Webhook received from %s: %s", sender, text)

    # Если нет текста или sender, просто 200
    if not sender or not text:
        return "OK", 200

    # Формируем ответ
    reply_text = f"Вы написали: «{text}»"

    # Параметры Send API
    url = "https://api.gupshup.io/wa/api/v1/msg"
    headers = {
        "apikey":       GUPSHUP_API_KEY,
        "Content-Type": "application/x-www-form-urlencoded"
    }
    payload = {
        "channel":     "whatsapp",
        "source":      GUPSHUP_SOURCE_NUMBER,
        "destination": sender,
        # Тело сообщения — JSON-строка
        "message":     '{"type":"text","text":"%s"}' % reply_text
    }

    # Логируем отправку
    app.logger.info("Sending Send-API payload: %s", payload)

    # Отправляем ответ через Gupshup
    resp = requests.post(url, headers=headers, data=payload)
    app.logger.info("Send-API responded %s: %s", resp.status_code, resp.text)

    # Всегда возвращаем 200
    return "OK", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
