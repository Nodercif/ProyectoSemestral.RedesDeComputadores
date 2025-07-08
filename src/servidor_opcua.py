from opcua import Server
import time
from datetime import datetime

def iniciar_servidor_opcua():
    # Configuración del servidor
    server = Server()
    server.set_endpoint("opc.tcp://0.0.0.0:4840")  # Escucha en todas las interfaces
    
    # Configura espacio de nombres
    uri = "urn:ejemplo:servidor-opcua"
    idx = server.register_namespace(uri)  # Registra un espacio de nombres único para el servidor
    
    # Crear objetos y variables
    objetos = server.get_objects_node()
    
    # Crear estructura de sensores
    sensores = objetos.add_object(idx, "Sensores")  # Crea un objeto llamado "Sensores" en el espacio de nombres registrado
    
    # Crear variables (con los mismos nodos que usa tu servidor intermedio)
    temperatura = sensores.add_variable("ns=2;i=123", "Temperatura", 0.0)
    humedad = sensores.add_variable("ns=2;i=124", "Humedad", 0.0)
    presion = sensores.add_variable("ns=2;i=125", "Presion", 0.0)
    
    # Hacer las variables editables para que puedan ser escritas por el cliente
    # Esto permite que los clientes puedan modificar los valores de estas variables
    temperatura.set_writable()
    humedad.set_writable()
    presion.set_writable()
    
    # Iniciar servidor
    server.start()
    print("\n=== Servidor OPC UA iniciado ===")
    print(f"Endpoint: opc.tcp://0.0.0.0:4840")
    print(f"Nodo Temperatura: ns=2;i=123")
    print(f"Nodo Humedad: ns=2;i=124")
    print(f"Nodo Presión: ns=2;i=125")
    print("="*30)
    print("Esperando datos...\n")
    
    try:
        while True:
            # Obtener valores actuales
            current_temp = temperatura.get_value()
            current_hum = humedad.get_value()
            current_pres = presion.get_value()
            
            # Mostrar solo si hay cambios
            if any([current_temp, current_hum, current_pres]):
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                print(f"[{timestamp}] Datos recibidos:")
                print(f"  → Temperatura: {current_temp:.2f}°C")
                print(f"  → Humedad: {current_hum:.2f}%")
                print(f"  → Presión: {current_pres:.2f} hPa")
                print("-"*40)
            
            time.sleep(0.5)  # Revisar valores cada medio segundo
            
    except KeyboardInterrupt:
        print("\nDeteniendo servidor...")
        server.stop()

if __name__ == "__main__":
    iniciar_servidor_opcua()