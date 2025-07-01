import os
from flask import Flask, request
import requests

app = Flask(__name__)

GUPSHUP_API_KEY       = os.environ["GUPSHUP_API_KEY"]
GUPSHUP_SOURCE_NUMBER = os.environ["GUPSHUP_SOURCE_NUMBER"]

@app.route("/gupshup", methods=["POST"])
def gupshup_webhook():
    data = request.get_json(force=True) or {}
    sender = data.get("sender") or data.get("from")
    text   = data.get("message", {}).get("text", "")

    if not sender or not text:
        return "OK", 200

    reply = f"Вы написали: «{text}»"

    url = "https://api.gupshup.io/wa/api/v1/msg"
    headers = {
        "apikey": GUPSHUP_API_KEY,
        "Content-Type": "application/x-www-form-urlencoded"
    }
    payload = {
        "channel":     "whatsapp",
        "source":      GUPSHUP_SOURCE_NUMBER,
        "destination": sender,
        # строка валидного JSON
        "message":     '{"type":"text","text":"%s"}' % reply
    }

    resp = requests.post(url, headers=headers, data=payload)
    app.logger.info("Send-API %s %s", resp.status_code, resp.text)
    return "OK", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
