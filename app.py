import os
from flask import Flask, request
import requests

app = Flask(__name__)

# В Variables на Railway нужно создать две переменные:
# GUPSHUP_API_KEY       = ваш sk_… ключ из Gupshup (Access API Keys)
# GUPSHUP_SOURCE_NUMBER = ваш WhatsApp-номер в Gupshup без '+', например '77021682964'
GUPSHUP_API_KEY       = os.environ["GUPSHUP_API_KEY"]
GUPSHUP_SOURCE_NUMBER = os.environ["GUPSHUP_SOURCE_NUMBER"]

@app.route("/gupshup", methods=["POST"])
def gupshup_webhook():
    data = request.get_json(force=True) or {}
    sender = data.get("sender") or data.get("from")
    text   = data.get("message", {}).get("text", "")

    # Логируем входящую пару
    app.logger.info("Webhook got: from=%s text=%s", sender, text)

    if not sender or not text:
        return "OK", 200

    reply_text = f"Вы написали: «{text}»"
    url = "https://api.gupshup.io/wa/api/v1/msg"
    headers = {
        "apikey":       GUPSHUP_API_KEY,
        "Content-Type": "application/x-www-form-urlencoded"
    }
    payload = {
        "channel":     "whatsapp",
        "source":      GUPSHUP_SOURCE_NUMBER,
        "destination": sender,
        "message":     '{"type":"text","text":"%s"}' % reply_text
    }

    # Логируем попытку отправки
    app.logger.info("Sending Send-API payload: %s", payload)
    resp = requests.post(url, headers=headers, data=payload)
    app.logger.info("Send-API responded %s: %s", resp.status_code, resp.text)

    return "OK", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    # debug=True позволит видеть логи в дев-сервере (какие-то WARNING можно игнорировать)
    app.run(host="0.0.0.0", port=port, debug=True)
