import os
import json
import logging
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# Переменные из окружения (укажите в Railway/Gupshup Dashboard)
GUPSHUP_API_KEY  = os.environ["GUPSHUP_API_KEY"]
GUPSHUP_APP_NAME = os.environ["GUPSHUP_APP_NAME"]  # точное имя App в Gupshup (регистрозависимо)
GUPSHUP_CAPI_URL = "https://api.gupshup.io/wa/api/v1/msg"

@app.route("/gupshup", methods=["GET"])
def verify():
    # Простая проверка, чтобы Gupshup принял ваш URL
    return "OK", 200

@app.route("/gupshup", methods=["POST"])
def webhook():
    data = request.get_json(force=True)
    # Само сообщение лежит в data["payload"]
    pl = data.get("payload", {})
    sender = pl.get("sender")
    text   = pl.get("message", {}).get("text")

    if not sender or not text:
        app.logger.error("Не получили sender/text в webhook: %s", json.dumps(data))
        return "Bad Request", 400

    # Готовим эхо-ответ
    payload = {
      "channel":     "whatsapp",
      "source":      sender,            # бот шлёт с того же номера
      "destination": sender,            # получатель — тот, кто написал
      "src.name":    GUPSHUP_APP_NAME,
      "message": json.dumps({
          "type": "text",
          "text": f"Эхо-ответ: {text}"
      })
    }

    headers = {
      "apikey":       GUPSHUP_API_KEY,
      "Content-Type": "application/x-www-form-urlencoded"
    }

    # Посылаем ответ через Gupshup CAPI
    resp = requests.post(GUPSHUP_CAPI_URL, data=payload, headers=headers)
    if resp.status_code != 200:
        app.logger.error("Ошибка при отправке ответа: %s — %s", resp.status_code, resp.text)
    else:
        app.logger.info("Отправили ответ: %s", resp.json())

    return jsonify({}), 200


if __name__ == "__main__":
    # В Railway дефолтный порт берётся из env PORT
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)
