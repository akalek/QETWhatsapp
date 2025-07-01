import os
import json
import logging
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# В переменных Railway или локально должны быть:
GUPSHUP_API_KEY  = os.environ.get("GUPSHUP_API_KEY", "")
GUPSHUP_APP_NAME = os.environ.get("GUPSHUP_APP_NAME", "")

# --- GET-запрос для верификации ---
@app.route("/gupshup", methods=["GET"])
def verify():
    # Gupshup просто проверяет, что URL отрабатывает 200
    return "OK", 200

# --- POST-запрос: сюда Gupshup шлёт входящие сообщения ---
@app.route("/gupshup", methods=["POST"])
def gupshup_webhook():
    data = request.get_json(force=True)
    sender = data.get("sender")
    text   = data.get("text")
    if not sender or not text:
        app.logger.error("Не получили sender/text в webhook")
        return "Bad Request", 400

    # Ответ бота — просто эхо
    payload = {
        "channel":      "whatsapp",
        "source":       GUPSHUP_APP_NAME,
        "destination":  sender,
        "message": json.dumps({
            "type": "text",
            "text": f"Вы написали: «{text}»"
        })
    }
    headers = {
        "apikey":       GUPSHUP_API_KEY,
        "Content-Type": "application/x-www-form-urlencoded"
    }
    resp = requests.post(
        "https://api.gupshup.io/wa/api/v1/msg",
        data=payload,
        headers=headers
    )
    if resp.status_code != 200:
        app.logger.error(f"Ошибка при отправке: {resp.status_code} — {resp.text}")
    return jsonify(status=resp.status_code), 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
