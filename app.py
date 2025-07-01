import os
import json
import requests
from flask import Flask, request

app = Flask(__name__)

# 1) Загрузка ваших товаров из products.json
with open("products.json", encoding="utf-8") as f:
    PRODUCTS = json.load(f)

# 2) Переменные окружения
GUPSHUP_API_KEY  = os.getenv("GUPSHUP_API_KEY", "")
GUPSHUP_APP_NAME = os.getenv("GUPSHUP_APP_NAME", "")

if not GUPSHUP_API_KEY or not GUPSHUP_APP_NAME:
    raise RuntimeError("Не задан GUPSHUP_API_KEY или GUPSHUP_APP_NAME")

@app.route("/gupshup", methods=["POST"])
def gupshup_webhook():
    # 3) Получаем тело вебхука от Gupshup
    payload = request.get_json(force=True)
    app.logger.info("Incoming payload: %s", json.dumps(payload, ensure_ascii=False))

    # 4) В Gupshup v2 текст и sender приходят так:
    #    payload["message"]["text"]  и  payload["message"]["sender"]
    msg = payload.get("message", {})
    sender = msg.get("sender")       # e.g. "whatsapp:+77081234567"
    text   = msg.get("text")         # e.g. "болгарка"

    if not sender or not text:
        app.logger.error("Не получили sender/text в webhook")
        return "", 400

    # 5) Чистим префикс и получаем просто номер
    dest = sender.split(":", 1)[-1]

    # 6) Ищем в вашей базе PRODUCTS тот товар, у которого text совпадает с любым из synonyms
    found = None
    for p in PRODUCTS:
        if text.lower() in (s.lower() for s in p.get("synonyms", [])):
            found = p
            break

    if found:
        reply = (
            f"🔎 Нашёл для вас:\n"
            f"{found['name']}\n"
            f"Мощность: {found['power']} Вт\n"
            f"Цена: {found['price_b2b']} тг\n"
            f"Ссылка: {found['kaspi_link']}"
        )
    else:
        reply = "Извините, я не нашёл такой инструмент в каталоге."

    # 7) Формируем форму для отправки через Gupshup CAPI
    form = {
        "channel":     "whatsapp",
        "source":      GUPSHUP_APP_NAME,
        "destination": dest,
        "message":     json.dumps({
            "type": "text",
            "text": reply
        }, ensure_ascii=False)
    }
    headers = {
        "apikey":       GUPSHUP_API_KEY,
        "Content-Type": "application/x-www-form-urlencoded"
    }

    # 8) Отправляем ответ
    r = requests.post(
        "https://api.gupshup.io/wa/api/v1/msg",
        headers=headers,
        data=form
    )
    if not r.ok:
        app.logger.error("Ошибка при отправке: %s — %s", r.status_code, r.text)

    return "", 200


if __name__ == "__main__":
    # В работе на Railway/Docker всегда дебаг off
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 8080)))
