import os
from flask import Flask, request
import requests

app = Flask(__name__)

# ← Убедитесь, что эти две переменные есть в Railway → Variables
GUPSHUP_API_KEY       = os.environ["GUPSHUP_API_KEY"]
GUPSHUP_SOURCE_NUMBER = os.environ["GUPSHUP_SOURCE_NUMBER"]

@app.route("/gupshup", methods=["POST"])
def gupshup_webhook():
    # 1) Получаем пришедший webhook
    data = request.get_json(force=True) or {}
    sender = data.get("sender") or data.get("from")
    text   = data.get("message", {}).get("text", "")

    # 2) Если нечего отвечать — сразу 200
    if not sender or not text:
        return "OK", 200

    # 3) Формируем ответ
    reply_text = f"Вы написали: «{text}»"

    # 4) Шлём его на Gupshup WhatsApp API
    url = "https://api.gupshup.io/wa/api/v1/msg"
    headers = {
        "apikey": GUPSHUP_API_KEY,
        "Content-Type": "application/x-www-form-urlencoded"
    }
    payload = {
        "channel":     "whatsapp",
        "source":      GUPSHUP_SOURCE_NUMBER,
        "destination": sender,
        # Тело сообщения — строка валидного JSON
        "message":     '{"type":"text","text":"%s"}' % reply_text
    }

    resp = requests.post(url, headers=headers, data=payload)
    # Выводим в логи ответ от Gupshup — чтобы убедиться, что статус 200 и есть messageId
    print("Gupshup Send-API →", resp.status_code, resp.text)

    # Завершаем webhook запрос
    return "OK", 200

if __name__ == "__main__":
    # Railway прокидывает порт в переменную PORT
    port = int(os.environ.get("PORT", 5000))
    # Flask dev-server — OK для Railway, warning можно игнорировать
    app.run(host="0.0.0.0", port=port)
