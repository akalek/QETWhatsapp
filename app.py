from flask import Flask, request, jsonify
import json

app = Flask(__name__)
with open("products.json", encoding="utf-8") as f:
    catalog = json.load(f)

def find_products(q, d, p):
    q = q.lower()
    candidates = [
      {**prod, "diff": abs(prod["power"] - p)}
      for prod in catalog
      if prod["diameter"] == d and
         any(s in q for s in prod["synonyms"])
    ]
    candidates.sort(key=lambda x: x["diff"])
    return candidates[:2]

@app.route("/gupshup", methods=["POST"])
def webhook():
    data = request.get_json()
    msg = data["message"]["text"]
    parts = msg.split()
    try:
        diameter = int(parts[-2])
        power    = int(parts[-1])
        query    = " ".join(parts[:-2])
    except:
        return jsonify({"message": {"type": "text", "text":
          "Пожалуйста, в формате: товар диаметр мощность\nПример: болгарка 125 1000"}})

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
        responses.append({"type":"image","url":prod["image_url"]})
        responses.append({"type":"text","text":text})

    return jsonify({"messages": responses})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
