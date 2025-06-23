import psycopg2
import pandas as pd

# Configura tu URL de base de datos (Render)
DATABASE_URL = "postgresql://qrdb_mq6o_user:QzNkFbGBSKMpKTh2kljkMUDe46LKJ9zh@dpg-d1a4je2dbo4c73c4qd9g-a.oregon-postgres.render.com:5432/qrdb_mq6o"

def exportar_a_excel():
    try:
        # Conectar a la base de datos
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        cursor = conn.cursor()

        # Ejecutar consulta para obtener todos los registros
        cursor.execute("""
            SELECT 
                numero_credencial, nombres, apellido_paterno, apellido_materno,
                email, telefono, rubro, sector, empresa, ubicacion, funcion_cargo,
                negocio, resumen, fecha_registro
            FROM credenciales
        """)

        # Obtener resultados y nombres de columnas
        columnas = [desc[0] for desc in cursor.description]
        datos = cursor.fetchall()

        # Crear DataFrame y exportar a Excel
        df = pd.DataFrame(datos, columns=columnas)
        df.to_excel("credenciales.xlsx", index=False)

        print("✅ Exportación completada: 'credenciales.xlsx'")
        cursor.close()
        conn.close()

    except Exception as e:
        print(f"❌ Error al exportar datos: {str(e)}")

if __name__ == "__main__":
    exportar_a_excel()
