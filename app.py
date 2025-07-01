import os
import requests
from flask import Flask, request, make_response

app = Flask(__name__)

# только POST-запросы требуют API-ключ, GET-запросы отвечаем просто OK
API_KEY     = os.environ["GUPSHUP_API_KEY"]   # sk_...
YOUR_NUMBER = os.environ["YOUR_NUMBER"]       # '77021682964'
APP_NAME    = os.environ["GUPSHUP_APP_NAME"]  # точное имя App из Dashboard

@app.route("/gupshup", methods=["GET", "POST"])
def gupshup_webhook():

    # 1) Простая проверка вебхука (GET) — просто возвращаем OK
    if request.method == "GET":
        return make_response("OK", 200)

    # 2) Разбор пришедшего сообщения (POST)
    data = request.get_json(force=True)

    sender = data.get("sender")              # номер клиента
    msg    = data.get("message", {})         
    text   = msg.get("text") if msg.get("type") == "text" else None

    if not sender or not text:
        app.logger.error("Не получили sender/text в webhook")
        return make_response("Bad Request", 400)

    # 3) Отправка in-session ответа
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

    if not resp.ok:
        app.logger.error(f"Ошибка отправки: {resp.status_code} — {resp.text}")

    return make_response("OK", 200)

if __name__ == "__main__":
    # на Railway порт берётся из $PORT, но 8080 тоже нормально
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
