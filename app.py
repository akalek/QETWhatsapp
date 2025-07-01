# app.py
import os
import logging
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# ENV-переменные (добавьте их в Settings→Variables на Railway)
GUPSHUP_API_KEY  = os.environ["GUPSHUP_API_KEY"]   # sk_xxx…
GUPSHUP_APP_ID   = os.environ["GUPSHUP_APP_ID"]    # App ID из Gupshup Settings, например ce…c59

@app.route("/gupshup", methods=["GET", "POST"])
def gupshup_webhook():
    # 1) Для проверки URL Gupshup при сохранении webhook:
    if request.method == "GET":
        return "OK", 200

    # 2) Обрабатываем Meta-вебхук v3
    data = request.get_json(force=True, silent=True) or {}
    # структура: { "entry":[ { "changes":[ { "value":{ "messages":[ ... ] } } ] } ] }
    try:
        entry   = data["entry"][0]
        change  = entry["changes"][0]
        value   = change["value"]
        messages = value.get("messages", [])
    except (KeyError, IndexError, TypeError):
        return "", 200

    if not messages:
        return "", 200

    m0     = messages[0]
    sender = m0.get("from")                             # номер отправителя
    text   = m0.get("text", {}).get("body")             # тело входящего текста

    if not sender or not text:
        return "", 200

    # 3) Формируем ответ
    reply = f"Вы написали: «{text}»"

    # 4) Шлём через Meta-CAPI Gupshup
    url = "https://api.gupshup.io/whatsapp/v1/messages"
    headers = {
        "apikey": GUPSHUP_API_KEY,
        "Content-Type": "application/json"
    }
    payload = {
        "appId": GUPSHUP_APP_ID,
        "to": sender,
        "type": "text",
        "text": { "body": reply }
    }

    resp = requests.post(url, json=payload, headers=headers, timeout=10)
    if not resp.ok:
        logging.error(f"Ошибка отправки в Gupshup Meta-CAPI {resp.status_code}: {resp.text}")

    # 5) Завершаем webhook 200, чтобы Gupshup не ретрайл
    return "", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
