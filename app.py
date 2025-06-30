import os
import json
from flask import Flask, request, jsonify

app = Flask(__name__)

# Загружаем каталог товаров из JSON
with open("products.json", encoding="utf-8") as f:
    catalog = json.load(f)

# Функция поиска товаров по запросу, диаметру и мощности
def find_products(query, diameter, power):
    q = query.lower()
    candidates = [
        {**prod, "diff": abs(prod["power"] - power)}
        for prod in catalog
        if prod.get("diameter") == diameter and
           any(s in q for s in prod.get("synonyms", []))
    ]
    # Сортируем по близости мощности и берём 2 варианта
    candidates.sort(key=lambda x: x["diff"])
    return candidates[:2]

# Вебхук для Gupshup (формат v2)
@app.route("/gupshup", methods=["POST"])
def webhook():
    data = request.get_json() or {}
    msg = data.get("message", {}).get("text", "")
    parts = msg.strip().split()

    # Ожидаем формат: товар диаметр мощность
    try:
        diameter = int(parts[-2])
        power    = int(parts[-1])
        query    = " ".join(parts[:-2])
    except (ValueError, IndexError):
        return jsonify({"message": {"type": "text",
            "text": (
                "Пожалуйста, пришлите запрос в формате: товар диаметр мощность\n"
                "Пример: болгарка 125 1000"
            )
        }})

    # Ищем подходящие товары
    matches = find_products(query, diameter, power)
    if not matches:
        return jsonify({"message": {"type": "text",
            "text": "Ничего не найдено по вашим параметрам."}})

    # Формируем ответ: фото + текст для каждого товара
    responses = []
    for prod in matches:
        text = (
            f"{prod['name']}\n"
            f"Диаметр: {prod['diameter']} мм\n"
            f"Мощность: {prod['power']} Вт\n"
            f"Цена для физ. лиц — смотрите в Kaspi:\n{prod['kaspi_link']}"
        )
        # Добавляем сначала медиа
        responses.append({"type": "image", "url": prod['image_url']})
        # Затем текст
        responses.append({"type": "text",  "text": text})

    return jsonify({"messages": responses})

# Точка входа для локальной и облачной работы
if __name__ == "__main__":
    # Берём порт из переменной окружения (Railway/Heroku и т.п.), иначе 5000
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
