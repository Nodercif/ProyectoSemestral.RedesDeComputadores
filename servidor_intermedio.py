import socket
import json
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from opcua import Client

def recibir_y_reenviar_tcp_opcua(
    host_tcp, puerto_tcp, 
    clave_publica_pem, 
    url_opcua, nodo_opcua
):
    # Cargar clave pública para verificar firma
    clave_publica = serialization.load_pem_public_key(clave_publica_pem)

    # Crear socket TCP
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s: # crea un nuevo socket al cual se le indica que el socket será de tipo stream (TCP) y lo usa como contexto para que cierre  automáticamente al salir del bloque with
        # Conectar al socket
        s.bind((host_tcp, puerto_tcp))                           # s.bind() establece la dirección y puerto
        s.listen(1)                                              # s.listen(1) permite una conexión entrante
        conexion, direccion = s.accept()                         # espera una conexión entrante y devuelve un nuevo socket para la conexión y la dirección del cliente
        with conexion:                                           # usa el socket de conexión como contexto para que se cierre automáticamente al salir del bloque with
            # Recibir datos: [firma][datos]
            datos_recibidos = conexion.recv(4096)                # recibe hasta 4096 bytes de datos del socket de conexión
            # Suponiendo que los primeros 256 bytes son la firma (RSA 2048)
            firma = datos_recibidos[:256]                        # extrae los primeros 256 bytes como la firma
            mensaje_binario = datos_recibidos[256:]              # el resto de los datos son el mensaje en binario

            # Verificar firma
            try:
                clave_publica.verify(
                    firma,
                    mensaje_binario,
                    padding.PKCS1v15(),                          # usa el padding PKCS1v15 para la verificación de la firma
                    hashes.SHA256()                              # usa el hash SHA256 para la verificación de la firma
                )
            # manejo de excepciones para verificar la firma
            except Exception as e: 
                print("Firma inválida:", e)
                return

            # Convertir binario a UTF-8 y cargar JSON
            try:
                mensaje_json = mensaje_binario.decode('utf-8')
                datos = json.loads(mensaje_json)
            # manejo de excepciones para decodificar el JSON
            except Exception as e:
                print("Error al decodificar JSON:", e)
                return

            # Enviar a servidor OPC UA
            cliente = Client(url_opcua)
            try:
                cliente.connect()
                nodo = cliente.get_node(nodo_opcua)
                nodo.set_value(datos)
                print("Datos enviados a OPC UA:", datos)
            finally:
                cliente.disconnect()