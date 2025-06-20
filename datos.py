import psycopg2

DATABASE_URL = "postgresql://qrdb_mq6o_user:QzNkFbGBSKMpKTh2kljkMUDe46LKJ9zh@dpg-d1a4je2dbo4c73c4qd9g-a.oregon-postgres.render.com/qrdb_mq6o"

try:
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    cur = conn.cursor()
    cur.execute("SELECT * FROM credenciales")
    rows = cur.fetchall()
    column_names = [desc[0] for desc in cur.description]

    print("Datos en la tabla credenciales:\n")
    for row in rows:
        for col, val in zip(column_names, row):
            print(f"{col}: {val}")
        print("-" * 40)

    cur.close()
    conn.close()
except Exception as e:
    print(f"❌ Error al conectar o consultar la base de datos: {e}")
