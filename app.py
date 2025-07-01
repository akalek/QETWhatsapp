import os
import requests
from flask import Flask, request

app = Flask(__name__)

# --- 1) Переменные окружения ---
GUPSHUP_API_KEY  = os.environ["GUPSHUP_API_KEY"]
GUPSHUP_APP_NAME = os.environ.get("GUPSHUP_APP_NAME", "")  # номер или имя вашего приложения

# --- 2) URL для отправки сообщений через Gupshup Send API ---
GUPSHUP_SEND_URL = "https://api.gupshup.io/sm/api/v1/msg"

@app.route("/gupshup", methods=["POST"])
def gupshup_webhook():
    data = request.get_json(force=True)
    app.logger.info("Incoming webhook payload: %s", data)

    # --- 3) Извлекаем номер отправителя из самых популярных полей ---
    sender = None
    if "sender" in data:
        sender = data["sender"]
    elif "source" in data:
        sender = data["source"]
    elif "payload" in data and isinstance(data["payload"], dict):
        p = data["payload"]
        sender = p.get("sender") or p.get("from") or p.get("chatId")
    # если так и не нашли — просто игнорируем
    if not sender:
        app.logger.warning("Не удалось найти поле отправителя, пропускаем")
        return "", 200

    # --- 4) Извлекаем текст входящего сообщения ---
    text = ""
    # формат v2
    if "message" in data and isinstance(data["message"], dict):
        text = data["message"].get("text") or ""
    # формат v3
    elif "text" in data:
        text = data["text"]

    # --- 5) Формируем ответ (эхо) ---
    reply = {
        "source":      GUPSHUP_APP_NAME,
        "destination": sender,
        "message": {
            "type": "text",
            "text": f"Вы написали: {text}"
        }
    }

    headers = {
        "apikey":       GUPSHUP_API_KEY,
        "Content-Type": "application/json"
    }

    # --- 6) Посылаем ответ в Gupshup Send API ---
    resp = requests.post(GUPSHUP_SEND_URL, json=reply, headers=headers)
    try:
        resp.raise_for_status()
    except requests.HTTPError as e:
        app.logger.error("Ошибка при отправке ответа: %s — %s", resp.status_code, resp.text)
        # возвращаем 200, чтобы Gupshup не дергал нас повторно—
        # а сам лог ошибки остаётся в приложении
        return "", 200

    return "", 200


if __name__ == "__main__":
    # порт Railway берёт из PORT, локально по умолчанию 8080
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
