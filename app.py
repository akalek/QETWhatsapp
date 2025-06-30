import os
import json
import requests
from flask import Flask, request

app = Flask(__name__)

# --- КОНФИГУРАЦИЯ (задать в Settings → Variables на Railway) ---
GUPSHUP_API_URL  = "https://api.gupshup.io/sm/api/v1/msg"
GUPSHUP_APP_NAME = os.environ["QwetAPItest"]  # из вашего Gupshup Dashboard, App settings → Name
GUPSHUP_API_KEY  = os.environ["sk_4e29a41731fd4ddbad63f0de680678aa"]   # ваш Gupshup API key (запросите у devsupport или из консоли)

# --- Загружаем каталог ---
with open("products.json", encoding="utf-8") as f:
    catalog = json.load(f)

def find_products(query, diameter, power):
    q = query.lower()
    cands = [
        {**prod, "diff": abs(prod.get("power",0) - power)}
        for prod in catalog
        if prod.get("diameter")==diameter and any(s in q for s in prod.get("synonyms",[]))
    ]
    cands.sort(key=lambda x: x["diff"])
    return cands[:2]

def send_msg(dest, msg_obj):
    """Отправить одно сообщение через Gupshup API."""
    payload = {
        "source":      GUPSHUP_APP_NAME,
        "destination": dest,
        "message":     msg_obj
    }
    headers = {
        "Content-Type": "application/json",
        "apikey":       GUPSHUP_API_KEY
    }
    resp = requests.post(GUPSHUP_API_URL, headers=headers, json=payload)
    # можно логировать: print("Gupshup send:", resp.status_code, resp.text)
    return resp

@app.route("/gupshup", methods=["POST"])
def webhook():
    data = request.get_json(silent=True) or {}
    # пропускаем все события кроме входящего сообщения
    if "message" not in data:
        return ("", 200)

    sender = data.get("sender")  # номер клиента
    text   = data["message"].get("text","").strip()
    parts  = text.split()
    # если не «товар диаметр мощность» — подсказка:
    try:
        diam  = int(parts[-2])
        power = int(parts[-1])
        query = " ".join(parts[:-2])
    except:
        help_msg = {
            "type":"text",
            "text":(
                "Пожалуйста, пришлите запрос в формате:\n"
                "товар диаметр мощность\n"
                "Пример: болгарка 125 1000"
            )
        }
        send_msg(sender, help_msg)
        return ("", 200)

    prods = find_products(query, diam, power)
    if not prods:
        send_msg(sender, {"type":"text","text":"Ничего не найдено по вашим параметрам."})
        return ("", 200)

    # отправляем сначала фото, затем текст по каждому из двух найденных
    for prod in prods:
        # картинка
        if prod.get("image_url"):
            send_msg(sender, {"type":"image", "url": prod["image_url"]})
        # текст
        text_block = (
            f"{prod['name']}\n"
            f"Диаметр: {prod['diameter']} мм\n"
            f"Мощность: {prod['power']} Вт\n"
            f"Цена для физ. лиц — смотрите в Kaspi:\n"
            f"{prod['kaspi_link']}"
        )
        send_msg(sender, {"type":"text", "text": text_block})

    return ("", 200)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
