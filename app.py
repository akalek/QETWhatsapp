import os
import json
from flask import Flask, request, jsonify

app = Flask(__name__)

# Загружаем каталог товаров из products.json
with open("products.json", encoding="utf-8") as f:
    catalog = json.load(f)

# Функция поиска товаров по запросу, диаметру и мощности
def find_products(query, diameter, power):
    q = query.lower()
    # Фильтруем товары по диаметру и синонимам
    candidates = [
        {**prod, "diff": abs(prod["power"] - power)}
        for prod in catalog
        if prod.get("diameter") == diameter and
           any(s in q for s in prod.get("synonyms", []))
    ]
    # Сортировка по минимальной разнице мощности и выбор первых двух
    candidates.sort(key=lambda x: x["diff"])
    return candidates[:2]

# Webhook для Gupshup (формат v2)
@app.route("/gupshup", methods=["POST"])
def webhook():
    # Попытка получить JSON без ошибки, даже если Content-Type не application/json
    data = request.get_json(silent=True) or {}
    # Если это не сообщение (например, Sent/Delivered webhook), просто отвечаем 200 OK
    if "message" not in data:
        return "", 200

    msg = data["message"].get("text", "").strip()
    parts = msg.split()
    # Ожидаем формат: товар диаметр мощность
    try:
        diameter = int(parts[-2])
        power = int(parts[-1])
        query = " ".join(parts[:-2])
    except (ValueError, IndexError):
        return jsonify({"message": {"type": "text", "text": (
            "Пожалуйста, пришлите запрос в формате: товар диаметр мощность\n"
            "Пример: болгарка 125 1000"
        )}})

    matches = find_products(query, diameter, power)
    if not matches:
        return jsonify({"message": {"type": "text", "text":
            "Ничего не найдено по вашим параметрам."}})

    responses = []
    for prod in matches:
        text = (
            f"{prod['name']}\n"
            f"Диаметр: {prod['diameter']} мм\n"
            f"Мощность: {prod['power']} Вт\n"
            f"Цена для физ. лиц — смотрите в Kaspi:\n{prod['kaspi_link']}"
        )
        responses.append({"type": "image", "url": prod["image_url"]})
        responses.append({"type": "text",  "text": text})

    return jsonify({"messages": responses})

# Точка входа: Flask слушает порт из переменной окружения PORT или 5000 по умолчанию
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
