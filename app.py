import os
from flask import Flask, request
import requests

app = Flask(__name__)

# Эти две переменные нужно добавить в настройки окружения Railway (или в ваш .env):
#   GUPSHUP_API_KEY        — ваш ключ вида sk_xxx...
#   GUPSHUP_SOURCE_NUMBER  — ваш Gupshup-номер (WhatsApp) без "+"
GUPSHUP_API_KEY   = os.environ["GUPSHUP_API_KEY"]
GUPSHUP_SOURCE_NO = os.environ["GUPSHUP_SOURCE_NUMBER"]

@app.route("/gupshup", methods=["POST"])
def gupshup_webhook():
    # Получаем JSON от Gupshup
    data = request.get_json(force=True, silent=True) or {}

    # В зависимости от формата payload, номер отправителя может быть в "sender" или "from"
    sender = data.get("sender") or data.get("from")
    # Извлекаем текст входящего сообщения
    text   = data.get("message", {}).get("text", "")

    # Если чего-то не хватило — просто вернём 200 без отправки
    if not sender or not text:
        return "OK", 200

    # Формируем ответ
    reply = f"Вы написали: «{text}»"

    # Отправляем его через Gupshup Send API
    url = "https://api.gupshup.io/wa/api/v1/msg"
    headers = {
        "apikey": GUPSHUP_API_KEY,
        "Content-Type": "application/x-www-form-urlencoded"
    }
    payload = {
        "channel":     "whatsapp",
        "source":      GUPSHUP_SOURCE_NO,
        "destination": sender,
        # В body ожидается строка валидного JSON
        "message":     '{"type":"text","text":"%s"}' % reply
    }

    resp = requests.post(url, headers=headers, data=payload)
    # Логируем результат (можно смотреть в Deploy Logs → HTTP Logs → Deploy Logs)
    app.logger.info("Send-API status=%s, body=%s", resp.status_code, resp.text)

    # Всегда отвечаем 200, чтобы Gupshup не пытался ретранслировать вебхук
    return "OK", 200

if __name__ == "__main__":
    # Порт Railway прокидывает в переменную PORT
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
