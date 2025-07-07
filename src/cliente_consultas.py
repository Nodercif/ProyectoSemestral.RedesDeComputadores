from opcua import Client
import time
from datetime import datetime

# Configuración OPC UA
OPCUA_URL = "opc.tcp://localhost:4840"
NODOS = {
    "temperatura": "ns=2;i=123",
    "humedad": "ns=2;i=124",
    "presion": "ns=2;i=125"
}

INTERVALO_SEGUNDOS = 5

# Umbrales de alerta (los mismos que tenías)
TEMP_MAX = 80
PRESION_MIN = 900
PRESION_MAX = 1500
HUMEDAD_MIN = 20
HUMEDAD_MAX = 90

def obtener_datos_opcua():
    client = Client(OPCUA_URL)
    try:
        client.connect()
        datos = {
            "id_sensor": 1,  # Puedes obtener esto de otro nodo si es necesario
            "timestamp": datetime.now().isoformat(),
            "temperatura": client.get_node(NODOS["temperatura"]).get_value(),
            "humedad": client.get_node(NODOS["humedad"]).get_value(),
            "presion": client.get_node(NODOS["presion"]).get_value()
        }
        return datos
    except Exception as e:
        print(f"Error OPC UA: {e}")
        return None
    finally:
        client.disconnect()

def revisar_alertas(medicion):
    alertas = []
    if medicion["temperatura"] > TEMP_MAX:
        alertas.append(f"Alta temperatura: {medicion['temperatura']} °C")
    if not (PRESION_MIN <= medicion["presion"] <= PRESION_MAX):
        alertas.append(f"Presión fuera de rango: {medicion['presion']} hPa")
    if not (HUMEDAD_MIN <= medicion["humedad"] <= HUMEDAD_MAX):
        alertas.append(f"Humedad fuera de rango: {medicion['humedad']} %")
    return alertas

def mostrar_alertas(alertas, medicion):
    if alertas:
        print(f"\nALERTA del sensor {medicion['id_sensor']} @ {medicion['timestamp']}")
        for alerta in alertas:
            print(alerta)
    else:
        print(f"Todo OK - Sensor {medicion['id_sensor']} @ {medicion['timestamp']}")

def main():
    print("Iniciando cliente de consulta OPC UA...")
    while True:
        try:
            datos = obtener_datos_opcua()
            if datos:
                alertas = revisar_alertas(datos)
                mostrar_alertas(alertas, datos)
            else:
                print("No se pudieron obtener datos del servidor OPC UA")
        except Exception as e:
            print("Error general:", e)

        time.sleep(INTERVALO_SEGUNDOS)

if __name__ == "__main__":
    main()