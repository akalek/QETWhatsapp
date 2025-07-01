import os
import requests
from flask import Flask, request

app = Flask(__name__)

GUPSHUP_API_KEY  = os.environ["GUPSHUP_API_KEY"]
GUPSHUP_APP_NAME = os.environ["GUPSHUP_APP_NAME"]  # точно как в Dashboard

@app.route("/gupshup", methods=["GET"])
def gupshup_verify():
    # Gupshup при добавлении вебхука посылает GET; мы просто отвечаем 200 OK
    return "OK", 200

@app.route("/gupshup", methods=["POST"])
def gupshup_webhook():
    data = request.get_json(force=True)
    app.logger.info("INCOMING: %s", data)

    sender = data.get("sender")
    text   = data.get("message", {}).get("text")
    if not sender or not text:
        app.logger.error("Не получили sender/text в webhook")
        return "", 400

    resp = requests.post(
        "https://api.gupshup.io/wa/api/v1/msg",
        headers={
            "apikey": GUPSHUP_API_KEY,
            "Content-Type": "application/x-www-form-urlencoded",
        },
        data={
            "channel":     "whatsapp",
            "source":      sender,
            "destination": sender,
            "src.name":    GUPSHUP_APP_NAME,
            "message":     f'{{"type":"text","text":"Вы написали: {text}"}}'
        }
    )

    try:
        resp.raise_for_status()
        return "", 200
    except Exception:
        app.logger.error("Ошибка ответа Gupshup CAPI %s: %s", resp.status_code, resp.text)
        return "", 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
