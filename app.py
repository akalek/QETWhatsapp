import os
import requests
from flask import Flask, request

app = Flask(__name__)

# -----------------------------------
# 1) Читаем из окружения
# -----------------------------------
GUPSHUP_API_KEY       = os.environ["GUPSHUP_API_KEY"]
GUPSHUP_SOURCE_NUMBER = os.environ["GUPSHUP_SOURCE_NUMBER"]

# -----------------------------------
# 2) Правильный эндпоинт для формы:
# -----------------------------------
WA_SEND_URL = "https://api.gupshup.io/wa/api/v1/msg"

@app.route("/gupshup", methods=["POST"])
def gupshup_webhook():
    data = request.get_json(force=True) or {}
    app.logger.info("Webhook payload: %s", data)

    # -----------------------------------
    # 3) Извлекаем телефон отправителя
    # -----------------------------------
    sender = data.get("sender") or data.get("source") \
          or data.get("payload", {}).get("sender") \
          or data.get("payload", {}).get("from")
    if not sender:
        app.logger.warning("No sender found, ignoring")
        return "", 200

    # -----------------------------------
    # 4) Извлекаем текст сообщения
    # -----------------------------------
    text = ""
    if "message" in data and isinstance(data["message"], dict):
        text = data["message"].get("text", "")
    else:
        text = data.get("text", "")

    # -----------------------------------
    # 5) Формируем ответ
    # -----------------------------------
    reply = f"Вы написали: «{text}»"
    payload = {
        "channel":     "whatsapp",
        "source":      GUPSHUP_SOURCE_NUMBER,
        "destination": sender,
        "message":     '{"type":"text","text":"%s"}' % reply
    }
    headers = {
        "apikey":        GUPSHUP_API_KEY,
        "Content-Type":  "application/x-www-form-urlencoded"
    }

    app.logger.info("Sending to WA API: %s", payload)
    resp = requests.post(WA_SEND_URL, headers=headers, data=payload)
    app.logger.info("WA API responded %s: %s", resp.status_code, resp.text)

    # Мы всегда возвращаем 200, чтобы Gupshup не дергал повторно
    return "", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    # debug=False безопасно для Railway, предупреждение можно игнорировать
    app.run(host="0.0.0.0", port=port, debug=False)
