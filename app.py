from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup
import os
import pandas as pd
from datetime import datetime

app = Flask(__name__)  # 👈 ESTA es la instancia que gunicorn necesita encontrar

ARCHIVO_EXCEL = "credenciales.xlsx"

# ---------- RUTA PARA LEER CREDENCIAL ----------
@app.route("/api/leer-credencial", methods=["POST"])
def leer_credencial():
    data = request.get_json()
    url = data.get("url")
    if not url:
        return jsonify({"error": "URL faltante"}), 400

    try:
        html = requests.get(url).text
        soup = BeautifulSoup(html, "html.parser")

        def leer_valor(id):
            tag = soup.find("input", id=id)
            return tag["value"].strip() if tag and tag.has_attr("value") else ""

        datos = {
            "numero_credencial": leer_valor("NumeroCredencial"),
            "tipo_credencial": leer_valor("TipoCredencial"),
            "nombres": leer_valor("Nombres"),
            "apellido_paterno": leer_valor("ApellidoPaterno"),
            "apellido_materno": leer_valor("ApellidoMaterno"),
            "email": leer_valor("Email"),
            "telefono": leer_valor("Telefono"),
        }

        return jsonify(datos)

    except Exception as e:
        return jsonify({"error": f"Error al procesar la URL: {str(e)}"}), 500

# ---------- RUTA PARA GUARDAR CREDENCIAL ----------
@app.route("/api/guardar-credencial", methods=["POST"])
def guardar_credencial():
    data = request.get_json()

    campos = [
        "numeroCredencial", "nombres", "apellidoPaterno", "apellidoMaterno",
        "email", "telefono", "rubro", "sector",
        "empresa", "ubicacion", "funcionCargo", "negocio", "resumen"
    ]

    if not all(campo in data for campo in campos):
        return jsonify({"error": "Faltan campos en el JSON"}), 400

    data["fecha_registro"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        if os.path.exists(ARCHIVO_EXCEL):
            df = pd.read_excel(ARCHIVO_EXCEL)
            if data["numeroCredencial"] in df["numeroCredencial"].astype(str).values:
                return jsonify({"mensaje": "La credencial ya fue registrada."}), 200
            df = pd.concat([df, pd.DataFrame([data])], ignore_index=True)
        else:
            df = pd.DataFrame([data])

        df.to_excel(ARCHIVO_EXCEL, index=False)
        return jsonify({"mensaje": "Credencial guardada exitosamente."})

    except Exception as e:
        return jsonify({"error": f"No se pudo guardar la credencial: {str(e)}"}), 500

# ---------- SOLO para correr localmente ----------
if __name__ == "__main__":
    app.run(debug=True)
