import os
import requests
from flask import Flask, request

app = Flask(__name__)

# Эти два значения надо определить в переменных окружения Railway (или локально перед запуском):
GUPSHUP_API_KEY  = os.environ["GUPSHUP_API_KEY"]   # ваш sk_… ключ
GUPSHUP_APP_NAME = os.environ["GUPSHUP_APP_NAME"]  # точное имя вашего App в Dashboard, например "QwetAPItest"

# Точка входа для вебхука Gupshup
@app.route("/gupshup", methods=["POST"])
def gupshup_webhook():
    data = request.get_json(force=True)
    # В формате v2 у вас будет поле "sender" и вложенный message.text
    sender = data.get("sender")
    text   = data.get("message", {}).get("text")

    if not sender or not text:
        app.logger.error("Не получили sender/text в webhook")
        return "", 400

    # Формируем payload для in-session ответа
    payload = {
        "channel":      "whatsapp",
        "source":       GUPSHUP_APP_NAME,
        "destination":  sender,
        "src.name":     GUPSHUP_APP_NAME,
        # message надо передать с JSON внутри form-data
        "message":      '{"type":"text","text":"Автоответ: %s"}' % text
    }

    headers = {
        "apikey":        GUPSHUP_API_KEY,
        "Content-Type":  "application/x-www-form-urlencoded"
    }

    # POST в Gupshup CAPI
    resp = requests.post(
        "https://api.gupshup.io/wa/api/v1/msg",
        data=payload,
        headers=headers,
        timeout=5
    )

    if resp.status_code != 200:
        app.logger.error(f"Ошибка при отправке ответа: {resp.status_code} — {resp.text}")
    else:
        app.logger.info(f"Отправлено сообщение: {resp.json()}")

    # Gupshup ждёт 200
    return "", 200

if __name__ == "__main__":
    # порт 8080 обязательный для Railway
    app.run(host="0.0.0.0", port=8080)
