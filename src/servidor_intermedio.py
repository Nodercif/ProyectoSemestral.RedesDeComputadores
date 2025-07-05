import socket
import json
import os
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from opcua import Client
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from pathlib import Path


def cargar_clave_publica():
    # Ruta relativa a la carpeta 'seguridad' dentro del proyecto
    ruta_clave = Path(__file__).parent.parent / "Seguridad" / "clave_publica.pem"
    
    try:
        with open(ruta_clave, "rb") as f:
            return f.read()
    except FileNotFoundError:
        raise Exception(
            f"No se encontró 'clave_publica.pem' en {ruta_clave}.\n"
            "Solución: Asegúrate de que existe la carpeta 'seguridad' con el archivo PEM."
        )

def main():

    # Configuración (ajusta estos valores)
    host_tcp = "localhost"
    puerto_tcp = 8080
    clave_publica_pem = cargar_clave_publica()                                                        # Cargar clave pública desde el archivo
    url_opcua = "opc.tcp://localhost:4840"
    nodo_opcua = "ns=2;i=123"

    # Cargar clave pública para verificar firma
    clave_publica = serialization.load_pem_public_key(clave_publica_pem)

    # Crear socket TCP
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:                                      # crea un nuevo socket al cual se le indica que el socket será de tipo stream (TCP) y lo usa como contexto para que cierre  automáticamente al salir del bloque with
        # Conectar al socket                                                                                                                                                                                                                                      
        s.bind((host_tcp, puerto_tcp))                                                                # s.bind() establece la dirección y puerto                                                                                                                          
        s.listen(1)                                                                                   # s.listen(1) permite una conexión entrante                                                                                                                         
        print(f"Servidor Intermedio escuchando en {host_tcp}:{puerto_tcp}...")  
        conexion, direccion = s.accept()                                                              # s.accept() acepta una conexión entrante y devuelve un nuevo socket de conexión y la dirección del cliente
        while True:
            try:
                conexion, direccion = s.accept()
                print(f"conexion entrante desde {direccion}")                                         # acepta una conexión entrante y devuelve un nuevo socket de conexión y la dirección del cliente                                                                                                                                                                          
                with conexion:                                                                        # usa el socket de conexión como contexto para que se cierre automáticamente al salir del bloque with                                                               
                    # Recibir datos: [firma][datos]                                                                                                                                                                                                                       
                    datos_recibidos = conexion.recv(4096)                                             # recibe hasta 4096 bytes de datos del socket de conexión                                                                                                           
                    if not datos_recibidos:  # Si no hay datos, cerrar
                        continue                                                                      # el resto de los datos son el mensaje en binario

                    # Procesar datos (tu código original)
                    firma = datos_recibidos[:256]
                    mensaje_binario = datos_recibidos[256:]

                    # Verificar firma
                    try:
                        clave_publica.verify(
                            firma,
                            mensaje_binario,
                            padding.PKCS1v15(),                                                       # usa el padding PKCS1v15 para la verificación de la firma
                            hashes.SHA256()                                                           # usa el hash SHA256 para la verificación de la firma
                        )
                        mensaje_json = mensaje_binario.decode('utf-8')
                        datos = json.loads(mensaje_json)
                        print("Datos verificados:", datos)

                        # Enviar a OPC UA
                        cliente = Client(url_opcua)
                        try:
                            cliente.connect()
                            nodo = cliente.get_node(nodo_opcua)
                            nodo.set_value(datos)
                            print("Enviado a OPC UA")
                        finally:
                            cliente.disconnect()

                    except Exception as e:
                        print(f" Error: {str(e)}")

            except KeyboardInterrupt:
                print("\n Servidor detenido manualmente")
                break

if __name__ == "__main__":
    main()