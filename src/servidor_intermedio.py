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
            "Solución: Asegúrate de que existe la carpeta 'Seguridad' con el archivo PEM."
        )

def main():
    # Configuración (ajusta estos valores)
    host_tcp = "localhost"
    puerto_tcp = 8080
    clave_publica_pem = cargar_clave_publica()  # Cargar clave pública desde el archivo
    url_opcua = "opc.tcp://localhost:4840"
    nodo_opcua = "ns=2;i=123"

    # Cargar clave pública para verificar firma
    clave_publica = serialization.load_pem_public_key(clave_publica_pem)

    # Crear socket TCP
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((host_tcp, puerto_tcp))
        s.listen(1)
        print(f"Servidor Intermedio escuchando en {host_tcp}:{puerto_tcp}...")
        
        while True:
            try:
                conexion, direccion = s.accept()
                print(f"\nConexión entrante desde: {direccion}")
                
                with conexion:
                    # Recibir primero la firma (256 bytes)
                    firma = conexion.recv(256)
                    if len(firma) != 256:
                        print("Error: Firma incompleta")
                        conexion.sendall(b"\x00")
                        continue
                    
                    # Recibir el JSON
                    datos_recibidos = b""
                    while True:
                        chunk = conexion.recv(4096)
                        if not chunk:
                            break
                        datos_recibidos += chunk
                        try:
                            mensaje_json = datos_recibidos.decode('utf-8')
                            json.loads(mensaje_json)  # Validar JSON
                            break
                        except (UnicodeDecodeError, json.JSONDecodeError):
                            continue

                    print(f"Firma recibida (hex): {firma.hex()[:20]}...")
                    print(f"JSON recibido: {datos_recibidos.decode('utf-8')[:100]}...")

                    try:
                        # Verificar firma
                        clave_publica.verify(
                            firma,
                            datos_recibidos,
                            padding.PKCS1v15(),
                            hashes.SHA256()
                        )
                        datos = json.loads(datos_recibidos.decode('utf-8'))
                        print("Datos verificados:", datos)
                        
                        # Enviar a OPC UA
                        cliente = Client(url_opcua)
                        try:
                            cliente.connect()
                            cliente.get_node(nodo_opcua).set_value(datos)
                            print("→ Enviado a OPC UA")
                            conexion.sendall(b"\x01")  # Confirmación EXITOSA
                        except Exception as opc_error:
                            print(f"Error OPC UA: {str(opc_error)}")
                            conexion.sendall(b"\x00")  # Confirmación FALLIDA
                        finally:
                            cliente.disconnect()

                    except Exception as e:
                        print(f"Error de verificación: {str(e)}")
                        conexion.sendall(b"\x00")

            except KeyboardInterrupt:
                print("\nServidor detenido manualmente")
                break
            except Exception as e:
                print(f"Error en conexión: {str(e)}")
                continue

if __name__ == "__main__":
    main()