# app.py
import os
import json
import logging
import requests
from flask import Flask, request

app = Flask(__name__, static_folder=None)
logging.basicConfig(level=logging.INFO)

# 1) Читаем из окружения
GUPSHUP_API_KEY  = os.environ["GUPSHUP_API_KEY"]
GUPSHUP_APP_NAME = os.environ["GUPSHUP_APP_NAME"]

# 2) Шаблон заголовков для CAPI-ответа
CAP_HEADERS = {
    "apikey": GUPSHUP_API_KEY,
    "Content-Type": "application/x-www-form-urlencoded",
}

@app.route("/gupshup", methods=["POST"])
def gupshup_webhook():
    data = request.get_json(force=True) or {}
    # --- Пример формата v2 webhook от Gupshup ---
    # {
    #   "sender": "7702XXXXXXX",
    #   "message": {"type":"text", "text":"привет"},
    #    ...
    # }
    sender = data.get("sender")
    text   = data.get("message", {}).get("text")

    if not sender or not text:
        app.logger.error("Не получили sender/text в webhook")
        return ("", 400)  # обязательно, чтобы Gupshup понял, что вы ошиблись

    # 3) Форма ответа по CAPI (in-session reply)
    form = {
        "channel"     : "whatsapp",
        "source"      : GUPSHUP_APP_NAME,
        "destination" : sender,
        "src.name"    : GUPSHUP_APP_NAME,
        # тело сообщения — строка JSON
        "message"     : json.dumps({
            "type":"text",
            "text": f"Вы сказали: «{text}»"
        })
    }

    try:
        resp = requests.post(
            "https://api.gupshup.io/wa/api/v1/msg",
            headers=CAP_HEADERS,
            data=form
        )
        resp.raise_for_status()
        app.logger.info("Отправили ответ в Gupshup CAPI, messageId=%s", resp.json().get("messageId"))
    except Exception as e:
        app.logger.error("Ошибка отправки в Gupshup CAPI %s: %s", getattr(e, "response", ""), e)
        # даже если сломалось, вернуть 200, иначе Gupshup зациклит попытки
        return ("", 200)

    return ("", 200)


if __name__ == "__main__":
    # для локального теста
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
