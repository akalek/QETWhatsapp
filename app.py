import os
import requests
from flask import Flask, request

app = Flask(__name__)

# 1) Забираем из окружения
GUPSHUP_API_KEY  = os.environ["GUPSHUP_API_KEY"]
# для WhatsApp-номера или точного имени вашего приложения
GUPSHUP_APP_NAME = os.environ["GUPSHUP_APP_NAME"]

# 2) Правильный эндпоинт для WhatsApp Send API
GUPSHUP_SEND_URL = "https://api.gupshup.io/wa/api/v1/msg"

@app.route("/gupshup", methods=["POST"])
def gupshup_webhook():
    data = request.get_json(force=True)
    app.logger.info("Incoming webhook: %s", data)

    # 3) Ищем, от кого пришло сообщение
    sender = data.get("sender") or data.get("source") \
          or data.get("payload",{}).get("sender") \
          or data.get("payload",{}).get("from")
    if not sender:
        app.logger.warning("Не нашли sender – пропускаем")
        return "", 200

    # 4) Собираем текст входящего
    text = ""
    msg = data.get("message", {})
    if isinstance(msg, dict):
        # Gupshup v2
        text = msg.get("text") or ""
    else:
        # возможно v3
        text = data.get("text", "")

    # 5) Формируем ответ
    payload = {
        "channel":     "whatsapp",
        "source":      GUPSHUP_APP_NAME,
        "destination": sender,
        "message": {
            "type": "text",
            "text": f"Вы написали: {text}"
        }
    }
    headers = {
        "apikey":       GUPSHUP_API_KEY,
        "Content-Type": "application/json"
    }

    # 6) Шлём ответ
    resp = requests.post(GUPSHUP_SEND_URL, json=payload, headers=headers)
    if resp.status_code != 200:
        app.logger.error("Send API error %s: %s", resp.status_code, resp.text)
    return "", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
