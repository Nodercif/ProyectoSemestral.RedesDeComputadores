from database import crear_tabla, insertar_medicion, obtener_todas
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

app = FastAPI()   #FastAPI es una librería para crear APIs RESTful de manera sencilla y rápida. Una API RESTful es un conjunto de reglas que permiten la comunicación entre diferentes sistemas a través de HTTP, utilizando métodos como GET, POST, PUT y DELETE para interactuar con recursos.

# Define un servidor FastAPI que recibe mediciones de sensores y las almacena en una base de datos SQLite.
class Medicion(BaseModel):  # BaseModel es una clase que permite definir modelos de datos y validarlos automáticamente.
    id: int
    timestamp: int
    temperatura: float
    presion: float
    humedad: float

crear_tabla()

@app.post("/mediciones")  # Define un endpoint POST para recibir mediciones de sensores.
async def recibir_medicion(medicion: Medicion):  # Recibe un objeto Medicion y lo valida automáticamente.
    insertar_medicion(medicion.id, medicion.timestamp, medicion.temperatura,
                      medicion.presion, medicion.humedad)
    return {"mensaje": "Medición guardada"}  

@app.get("/mediciones")
async def listar_mediciones():
    datos = obtener_todas()
    return [
        {
            "id_sensor": d[0],
            "timestamp": d[1],
            "temperatura": d[2],
            "presion": d[3],
            "humedad": d[4],
        }
        for d in datos
    ]

@app.get("/", response_class=HTMLResponse)  # Devuelve una página HTML.
async def visualizar():
    datos = obtener_todas()
    filas = "".join(
        f"<tr><td>{d[0]}</td><td>{d[1]}</td><td>{d[2]}</td><td>{d[3]}</td><td>{d[4]}</td></tr>"
        for d in datos
    )  # Crea filas de la tabla HTML con los datos obtenidos de la base de datos.
    return f"""
    <html>
    <head><title>Visualización de Datos</title></head>
    <body>
    <h1>Últimas Mediciones</h1>
    <table border="1">
        <tr><th>ID</th><th>Timestamp</th><th>Temp</th><th>Presión</th><th>Humedad</th></tr>
        {filas}
    </table>
    </body>
    </html>
    """
