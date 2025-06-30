import time

import httpx

API_URL = "http://127.0.0.1:8000/mediciones"
INTERVALO_SEGUNDOS = 5

TEMP_MAX = 80
PRESION_MIN = 900
PRESION_MAX = 1500
HUMEDAD_MIN = 20
HUMEDAD_MAX = 90

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
    print("Iniciando cliente de consulta...")
    while True:
        try:
            respuesta = httpx.get(API_URL)
            if respuesta.status_code == 200:
                datos = respuesta.json()
                if not datos:
                    print("No hay datos disponibles aún.")
                else:
                    ultima = datos[0]
                    alertas = revisar_alertas(ultima)
                    mostrar_alertas(alertas, ultima)
            else:
                print("Error al consultar la API:", respuesta.status_code)
        except Exception as e:
            print("Error de conexión:", e)

        time.sleep(INTERVALO_SEGUNDOS)

if __name__ == "__main__":
    main()
