import os
import requests
from flask import Flask, request, make_response

app = Flask(__name__)

# 1) VERIFY_TOKEN — любая строка, но она же должна быть в настройках вебхука
VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN", "my_verify_token")

# 2) API_KEY — ваш Gupshup API-ключ (sk_...)
API_KEY = os.environ["GUPSHUP_API_KEY"]

# 3) YOUR_NUMBER — номер в формате «77021682964» (без +)
YOUR_NUMBER = os.environ.get("YOUR_NUMBER", "77021682964")

# 4) APP_NAME — точное имя вашего приложения (src.name)
APP_NAME = os.environ["GUPSHUP_APP_NAME"]

@app.route("/gupshup", methods=["GET", "POST"])
def gupshup_webhook():

    # === GET VERIFICATION ===
    if request.method == "GET":
        mode      = request.args.get("hub.mode")
        token     = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")
        if mode == "subscribe" and token == VERIFY_TOKEN and challenge:
            return make_response(challenge, 200)
        return make_response("Forbidden", 403)

    # === POST MESSAGE HANDLING ===
    data = request.get_json(force=True)

    # У Gupshup v2 поле sender идёт на верхнем уровне
    sender = data.get("sender")
    msg    = data.get("message", {})
    text   = msg.get("text") if msg.get("type") == "text" else None

    if not sender or not text:
        app.logger.error("Не получили sender/text в webhook")
        return make_response("Bad Request", 400)

    # === SEND IN-SESSION REPLY ===
    resp = requests.post(
        "https://api.gupshup.io/wa/api/v1/msg",
        headers={
            "apikey": API_KEY,
            "Content-Type": "application/x-www-form-urlencoded"
        },
        data={
            "channel":     "whatsapp",
            "source":      YOUR_NUMBER,                     # <-- ваш WhatsApp-номер
            "destination": sender,                          # <-- обратно клиенту
            "src.name":    APP_NAME,                        # <-- точно как в Dashboard
            "message":     f'{{"type":"text","text":"Вы сказали: {text}"}}'
        }
    )

    if not resp.ok:
        app.logger.error(f"Ошибка при отправке: {resp.status_code} — {resp.text}")

    return make_response("OK", 200)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
