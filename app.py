import os
import logging
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# эти переменные нужно добавить в Settings → Variables на Railway
GUPSHUP_API_KEY   = os.environ["GUPSHUP_API_KEY"]    # ваш sk_… API-ключ из Settings → API Keys
GUPSHUP_APP_NAME  = os.environ["GUPSHUP_APP_NAME"]   # точное имя вашего приложения (App name) из Dashboard

@app.route("/gupshup", methods=["GET", "POST"])
def gupshup_webhook():
    # --- webhook verification (Gupshup делает GET при сохранении URL) ---
    if request.method == "GET":
        return "OK", 200

    # --- обработка входящего v2-сообщения ---
    data = request.get_json(force=True, silent=True) or {}
    # ожидаем структуру: { "sender":"7702…", "message":{ "text":"привет" }, … }
    sender = data.get("sender")
    msg    = data.get("message", {}).get("text")

    if not sender or not msg:
        # неверный формат — просто молча возвращаем 200
        return "", 200

    logging.info(f"Входящее от {sender}: {msg}")

    # --- формируем ответ ---
    reply = f"Вы написали: «{msg}»"

    # --- шлём обратно через CP API v2 ---
    url = "https://api.gupshup.io/sm/api/v1/msg"
    headers = {
        "apikey": GUPSHUP_API_KEY,
        "Content-Type": "application/json"
    }
    payload = {
        "source":      GUPSHUP_APP_NAME,
        "destination": sender,
        "message": {
            "type": "text",
            "text": reply
        }
    }

    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=10)
        resp.raise_for_status()
        logging.info(f"Ответ отправлен, id={resp.json().get('messageId')}")
    except Exception as e:
        logging.error(f"Ошибка отправки в Gupshup v2: {e}")

    # отдаём 200, чтобы Gupshup не ретрайл
    return "", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
