import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# Берём из переменных окружения
GUPSHUP_API_KEY   = os.environ["GUPSHUP_API_KEY"]
GUPSHUP_APP_NAME  = os.environ["GUPSHUP_APP_NAME"]   # ваш номер или имя приложения
GUPSHUP_API_URL   = os.environ.get(
    "GUPSHUP_API_URL",
    "https://api.gupshup.io/wa/api/v1/msg"         # новый endpoint для WhatsApp CAPI
)

@app.route("/gupshup", methods=["POST"])
def gupshup_webhook():
    data = request.get_json(force=True)
    # распакуем sender и текст
    sender = data["sender"]
    text   = data.get("message", {}).get("text", "")
    # формируем ответ
    reply = f"Вы написали: «{text}»"

    payload = {
        "channel":     "whatsapp",
        "source":      GUPSHUP_APP_NAME,
        "destination": sender,
        "message": {
            "type": "text",
            "text": {"body": reply}
        }
    }
    headers = {
        "apikey":       GUPSHUP_API_KEY,
        "Content-Type": "application/json"
    }
    resp = requests.post(GUPSHUP_API_URL, headers=headers, json=payload)
    resp.raise_for_status()

    return jsonify({"status": "sent"}), 200

if __name__ == "__main__":
    # Railway ждёт, что вы подхватите $PORT
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
