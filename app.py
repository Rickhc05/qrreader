from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import psycopg2
import os
import json

app = Flask(__name__)

# 🔐 Conexión PostgreSQL (Render)
DATABASE_URL = "postgresql://qrdb_mq6o_user:QzNkFbGBSKMpKTh2kljkMUDe46LKJ9zh@dpg-d1a4je2dbo4c73c4qd9g-a.oregon-postgres.render.com:5432/qrdb_mq6o"

# 📄 Ruta al archivo JSON local
JSON_PATH = os.path.join(os.path.dirname(__file__), "map_pe.json")

def get_connection():
    return psycopg2.connect(DATABASE_URL, sslmode='require')

# ---------- LECTURA DE DATOS POR SCRAPING ----------
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

# ---------- GUARDAR O ACTUALIZAR CREDENCIAL ----------
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

        # Verificar si ya existe
        cur.execute("SELECT COUNT(*) FROM credenciales WHERE numero_credencial = %s", (data["numeroCredencial"],))
        existe = cur.fetchone()[0] > 0

        if existe:
            # 🔁 ACTUALIZAR
            cur.execute("""
                UPDATE credenciales SET
                    nombres = %s,
                    apellido_paterno = %s,
                    apellido_materno = %s,
                    email = %s,
                    telefono = %s,
                    rubro = %s,
                    sector = %s,
                    empresa = %s,
                    ubicacion = %s,
                    funcion_cargo = %s,
                    negocio = %s,
                    resumen = %s,
                    fecha_registro = %s
                WHERE numero_credencial = %s
            """, (
                data["nombres"], data["apellidoPaterno"], data["apellidoMaterno"],
                data["email"], data["telefono"], data["rubro"], data["sector"],
                data["empresa"], data["ubicacion"], data["funcionCargo"], data["negocio"],
                data["resumen"], data["fecha_registro"],
                data["numeroCredencial"]
            ))
            conn.commit()
            cur.close()
            conn.close()
            return jsonify({"mensaje": "Credencial actualizada correctamente."})

        else:
            # ➕ INSERTAR
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
        return jsonify({"error": f"No se pudo guardar/actualizar la credencial: {str(e)}"}), 500

# ---------- VERIFICAR SI EXISTE CREDENCIAL ----------
@app.route("/api/verificar-credencial", methods=["POST"])
def verificar_credencial():
    data = request.get_json()
    numero = data.get("numeroCredencial")

    if not numero:
        return jsonify({"error": "Número inválido"}), 400

    try:
        resultado = buscar_credencial_por_numero(numero)
        if resultado:
            return jsonify({"registrado": True, "datos": resultado})
        else:
            return jsonify({"registrado": False})
    except Exception as e:
        return jsonify({"error": f"No se pudo verificar la credencial: {str(e)}"}), 500

# ---------- BUSCAR UNA CREDENCIAL POR NÚMERO ----------
def buscar_credencial_por_numero(numero):
    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute("""
            SELECT 
                numero_credencial, nombres, apellido_paterno, apellido_materno,
                email, telefono, rubro, sector, empresa, ubicacion, funcion_cargo,
                negocio, resumen
            FROM credenciales
            WHERE numero_credencial = %s
        """, (numero,))

        fila = cur.fetchone()
        cur.close()
        conn.close()

        if fila:
            return {
                "numeroCredencial": fila[0],
                "nombres": fila[1],
                "apellidoPaterno": fila[2],
                "apellidoMaterno": fila[3],
                "email": fila[4],
                "telefono": fila[5],
                "rubro": fila[6],
                "sector": fila[7],
                "empresa": fila[8],
                "ubicacion": fila[9],
                "funcionCargo": fila[10],
                "negocio": fila[11],
                "resumen": fila[12]
            }
        else:
            return None
    except Exception as e:
        cur.close()
        conn.close()
        raise e

# ---------- EMPRESAS DESDE BD O JSON ----------
@app.route("/api/empresas", methods=["GET"])
def obtener_empresas():
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT DISTINCT empresa FROM credenciales WHERE empresa IS NOT NULL AND empresa <> ''")
        empresas = [row[0] for row in cur.fetchall()]
        cur.close()
        conn.close()

        if not empresas:
            empresas = leer_desde_json("empresas")
        return jsonify(empresas)
    except Exception:
        return jsonify(leer_desde_json("empresas"))

@app.route("/api/ubicaciones", methods=["GET"])
def obtener_ubicaciones():
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT DISTINCT ubicacion FROM credenciales WHERE ubicacion IS NOT NULL AND ubicacion <> ''")
        ubicaciones = [row[0] for row in cur.fetchall()]
        cur.close()
        conn.close()

        if not ubicaciones:
            ubicaciones = leer_desde_json("ubicaciones")
        return jsonify(ubicaciones)
    except Exception:
        return jsonify(leer_desde_json("ubicaciones"))

def leer_desde_json(clave):
    try:
        with open(JSON_PATH, encoding="utf-8") as f:
            data = json.load(f)
            return data.get(clave, [])
    except Exception as e:
        print(f"Error al leer JSON: {e}")
        return []

@app.route("/api/debug-json", methods=["GET"])
def debug_json():
    try:
        with open(JSON_PATH, encoding="utf-8") as f:
            data = json.load(f)
            return jsonify({"empresas": data.get("empresas", []), "ubicaciones": data.get("ubicaciones", [])})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ---------- EJECUCIÓN LOCAL ----------
if __name__ == "__main__":
    app.run(debug=False)