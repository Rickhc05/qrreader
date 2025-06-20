from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import psycopg2

app = Flask(__name__)

# 🔐 Cadena de conexión directa (no recomendable en producción)
DATABASE_URL = "postgresql://qrdb_mq6o_user:QzNkFbGBSKMpKTh2kljkMUDe46LKJ9zh@dpg-d1a4je2dbo4c73c4qd9g-a.oregon-postgres.render.com:5432/qrdb_mq6o"

def get_connection():
    return psycopg2.connect(DATABASE_URL, sslmode='require')

# ---------- RUTA PARA LEER CREDENCIAL (SCRAPING) ----------
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

# ---------- RUTA PARA GUARDAR CREDENCIAL EN PostgreSQL ----------
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
        conn = get_connection()
        cur = conn.cursor()

        # Verificar duplicado
        cur.execute("SELECT COUNT(*) FROM credenciales WHERE numero_credencial = %s", (data["numeroCredencial"],))
        if cur.fetchone()[0] > 0:
            return jsonify({"mensaje": "La credencial ya fue registrada."}), 200

        # Insertar nueva fila
        cur.execute("""
            INSERT INTO credenciales (
                numero_credencial, nombres, apellido_paterno, apellido_materno,
                email, telefono, rubro, sector, empresa, ubicacion, funcion_cargo,
                negocio, resumen, fecha_registro
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            data["numeroCredencial"], data["nombres"], data["apellidoPaterno"], data["apellidoMaterno"],
            data["email"], data["telefono"], data["rubro"], data["sector"],
            data["empresa"], data["ubicacion"], data["funcionCargo"], data["negocio"],
            data["resumen"], data["fecha_registro"]
        ))

        conn.commit()
        cur.close()
        conn.close()

        return jsonify({"mensaje": "Credencial guardada exitosamente."})

    except Exception as e:
        return jsonify({"error": f"No se pudo guardar la credencial: {str(e)}"}), 500
    


@app.route("/api/verificar-credencial", methods=["POST"])
def verificar_credencial():
    data = request.json
    numero = data.get("numeroCredencial")

    if not numero:
        return jsonify({"error": "Número inválido"}), 400

    # Suponiendo que estás usando una base de datos con búsqueda
    resultado = buscar_credencial_por_numero(numero)

    if resultado:
        return jsonify({"registrado": True, "datos": resultado})
    else:
        return jsonify({"registrado": False})


# ---------- SOLO PARA LOCAL ----------
if __name__ == "__main__":
    app.run(debug=True)
