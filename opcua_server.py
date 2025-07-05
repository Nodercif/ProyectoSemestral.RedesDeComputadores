from opcua import Server

def run_opcua_server():
    server = Server()
    server.set_endpoint("opc.tcp://localhost:4840")
    
    # Configurar espacio de nombres
    uri = "http://ejemplo.com/sensores"
    idx = server.register_namespace(uri)
    
    # Crear nodos
    objects = server.get_objects_node()
    sensor = objects.add_object(idx, "Sensores")
    temp = sensor.add_variable(idx, "Temperatura", 0.0)
    temp.set_writable()
    
    print("Servidor OPC UA iniciado en opc.tcp://localhost:4840")
    try:
        server.start()
        while True:
            pass
    except KeyboardInterrupt:
        print("Deteniendo servidor OPC UA...")
    finally:
        server.stop()

if __name__ == "__main__":
    run_opcua_server()