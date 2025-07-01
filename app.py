import os
import requests
from flask import Flask, request

app = Flask(__name__)

# 1) Берём из ENV ключ и App ID
GUPSHUP_API_KEY = os.environ["GUPSHUP_API_KEY"]
GUPSHUP_APP_ID  = os.environ["GUPSHUP_APP_ID"]

# 2) Новый CAPI-эндпоинт
GUPSHUP_SEND_URL = "https://api.gupshup.io/whatsapp/v1/messages"

@app.route("/gupshup", methods=["POST"])
def gupshup_webhook():
    data = request.get_json(force=True)
    app.logger.info("Incoming webhook: %s", data)

    # 3) Поле sender может быть в разных местах, попробуем несколько вариантов
    sender = (
        data.get("sender")
        or data.get("source")
        or data.get("payload", {}).get("sender")
        or data.get("payload", {}).get("from")
    )
    if not sender:
        app.logger.warning("Не могу найти номер отправителя, пропускаю")
        return "", 200

    # 4) Считываем текст входящего сообщения
    text = ""
    if "message" in data and isinstance(data["message"], dict):
        text = data["message"].get("text") or ""
    else:
        text = data.get("text", "")

    # 5) Готовим новый payload под CAPI-запрос
    payload = {
        "appId": GUPSHUP_APP_ID,
        "to": sender,
        "type": "text",
        "text": {
            "body": f"Вы написали: {text}"
        }
    }
    headers = {
        "apikey":        GUPSHUP_API_KEY,
        "Content-Type":  "application/json"
    }

    # 6) Отправляем ответ
    resp = requests.post(GUPSHUP_SEND_URL, json=payload, headers=headers)
    if resp.status_code != 201 and resp.status_code != 200:
        app.logger.error(
            "Ошибка отправки в Gupshup CAPI %s: %s",
            resp.status_code, resp.text
        )
    else:
        app.logger.info("Успешно отправили ответ, messageId: %s",
                        resp.json().get("messageId"))
    return "", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
