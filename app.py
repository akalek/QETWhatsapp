# app.py
import os
import requests
from flask import Flask, request, make_response

app = Flask(__name__)

API_KEY     = os.environ["GUPSHUP_API_KEY"]
YOUR_NUMBER = os.environ["YOUR_NUMBER"]       # ваш WhatsApp-номер, например "77021682964"
APP_NAME    = os.environ["GUPSHUP_APP_NAME"]  # src.name из Dashboard

@app.route("/gupshup", methods=["GET", "POST"])
def webhook():
    # === Логика проверочного GET ===
    if request.method == "GET":
        # НИЧЕГО не должно проверяться — просто 200 OK
        return make_response("OK", 200)

    # === Логика обработки POST ===
    data = request.get_json(force=True)
    sender = data.get("sender")
    text   = data.get("message", {}).get("text")
    if not sender or text is None:
        # возвращаем 400 только если POST реально некорректный
        return make_response("Bad Request", 400)

    # === Отправка echo-ответа ===
    resp = requests.post(
        "https://api.gupshup.io/wa/api/v1/msg",
        headers={
            "apikey": API_KEY,
            "Content-Type": "application/x-www-form-urlencoded"
        },
        data={
            "channel":     "whatsapp",
            "source":      YOUR_NUMBER,
            "destination": sender,
            "src.name":    APP_NAME,
            "message":     f'{{"type":"text","text":"Вы сказали: {text}"}}'
        }
    )
    return make_response("OK", 200)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
