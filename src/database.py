import sqlite3  # Base de datos SQLite para almacenar las mediciones

DB_NAME = 'datos.db'

def crear_tabla():
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS mediciones (
                id_sensor INTEGER,
                timestamp INTEGER,
                temperatura REAL,
                presion REAL,
                humedad REAL
            )
        ''')

def insertar_medicion(id_sensor, timestamp, temperatura, presion, humedad):
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute('''
            INSERT INTO mediciones (id_sensor, timestamp, temperatura, presion, humedad)
            VALUES (?, ?, ?, ?, ?)
        ''', (id_sensor, timestamp, temperatura, presion, humedad))

def obtener_todas():
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.execute('SELECT * FROM mediciones ORDER BY timestamp DESC')
        return cursor.fetchall()
