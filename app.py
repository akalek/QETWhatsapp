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
    data = request.get_json(silent=True) or {}
    # Если это не сообщение (например, delivery, sent), возвращаем 200 без контента
    if "message" not in data:
        return "", 200

    msg = data["message"].get("text", "").strip()
    parts = msg.split()
    # Если запрос не в формате "товар диаметр мощность", отвечаем с подсказкой
    try:
        diameter = int(parts[-2])
        power = int(parts[-1])
        query = " ".join(parts[:-2])
    except (ValueError, IndexError):
        fallback = {"type": "text", "text": (
            "Пожалуйста, пришлите запрос в формате: товар диаметр мощность
"
            "Пример: болгарка 125 1000"
        )}
        return jsonify({"messages": [fallback]})

    matches = find_products(query, diameter, power)
    if not matches:
        nores = {"type": "text", "text": "Ничего не найдено по вашим параметрам."}
        return jsonify({"messages": [nores]})

    responses = []
    for prod in matches:
        text = (
            f"{prod['name']}
"
            f"Диаметр: {prod['diameter']} мм
"
            f"Мощность: {prod['power']} Вт
"
            f"Цена для физ. лиц — смотрите в Kaspi:
{prod['kaspi_link']}"
        )
        responses.append({"type": "image", "url": prod["image_url"]})
        responses.append({"type": "text",  "text": text})

    return jsonify({"messages": responses})

# Точка входа: Flask слушает порт из переменной окружения PORT или 5000 по умолчанию
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
