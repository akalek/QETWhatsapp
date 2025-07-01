import os
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# Ваш GUPSHUP API ключ (берётся из переменной окружения на Railway, Heroku и т.д.)
GUPSHUP_API_KEY = os.environ.get("GUPSHUP_API_KEY", "sk_b63ae292d5484ca6ba3f0143838edb32")
# Имя вашего WhatsApp-приложения в Gupshup (Access API → App Name)
GUPSHUP_APP_NAME = os.environ.get("GUPSHUP_APP_NAME", "QwetAPItest")

# Ендпоинт Gupshup для отправки сообщений
GUPSHUP_SEND_URL = "https://api.gupshup.io/sm/api/v1/msg"

@app.route("/gupshup", methods=["POST"])
def gupshup_webhook():
    data = request.get_json(force=True)
    # Получили текст от пользователя
    incoming_text = data.get("message", {}).get("text", "")
    sender = data.get("sender") or data.get("source")
    
    # Подготовим простой эхо-ответ
    reply_text = f"Вы написали: {incoming_text}"
    
    # Тело запроса к Gupshup Send API
    payload = {
        "source": GUPSHUP_APP_NAME,     
        "destination": sender,          
        "message": {
            "type": "text",
            "text": reply_text
        }
    }
    headers = {
        "Content-Type": "application/json",
        "apikey": GUPSHUP_API_KEY
    }
    
    # Вызываем Gupshup API, чтобы отправить ответ пользователю
    resp = requests.post(GUPSHUP_SEND_URL, json=payload, headers=headers)
    resp.raise_for_status()
    
    # Gupshup ждёт от нас HTTP 200 и пустое тело
    return "", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
