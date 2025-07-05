import socket
import json
import os
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from opcua import Client, Server
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from pathlib import Path

def cargar_clave_publica():
    ruta_clave = Path(__file__).parent.parent / "Seguridad" / "clave_publica.pem"
    
    try:
        with open(ruta_clave, "rb") as f:
            return f.read()
    except FileNotFoundError:
        raise Exception(
            f"No se encontró 'clave_publica.pem' en {ruta_clave}.\n"
            "Solución: Asegúrate de que existe la carpeta 'Seguridad' con el archivo PEM."
        )

def verificar_conexion_opcua(url):
    """Paso 1 de diagnóstico: Verificar conexión OPC UA"""
    print("\n=== Diagnóstico OPC UA ===")
    print("Paso 1: Verificando conexión al servidor OPC UA...")
    client = Client(url)
    try:
        client.connect()
        print("✓ Conexión OPC UA exitosa!")
        client.disconnect()
        return True
    except Exception as e:
        print(f"✗ Error conectando a OPC UA: {e}")
        return False
    finally:
        try:
            client.disconnect()
        except:
            pass

def verificar_nodo_opcua(url, nodo):
    """Paso 2 de diagnóstico: Verificar nodo OPC UA"""
    print("\nPaso 2: Verificando nodo OPC UA...")
    client = Client(url)
    try:
        client.connect()
        try:
            node = client.get_node(nodo)
            valor = node.get_value()
            print(f"✓ Nodo encontrado. Valor actual: {valor}")
            return True
        except Exception as e:
            print(f"✗ Error accediendo al nodo: {e}")
            return False
    except Exception as e:
        print(f"✗ Error de conexión durante verificación de nodo: {e}")
        return False
    finally:
        try:
            client.disconnect()
        except:
            pass

def crear_nodo_opcua_si_no_existe(url, nodo):
    """Paso 3 de diagnóstico: Crear nodo si no existe"""
    print("\nPaso 3: Intentando crear nodo si no existe...")
    server = Server()
    try:
        server.set_endpoint(url)
        server.start()
        objects = server.get_objects_node()
        
        # Crear estructura básica si no existe
        try:
            myobj = objects.add_object(2, "Sensores")
            myvar = myobj.add_variable(nodo, "DatosSensor", 0.0)
            myvar.set_writable()
            print(f"✓ Nodo creado exitosamente: {nodo}")
            return True
        except Exception as e:
            print(f"✗ Error creando nodo: {e}")
            return False
    except Exception as e:
        print(f"✗ Error iniciando servidor OPC UA temporal: {e}")
        return False
    finally:
        try:
            server.stop()
        except:
            pass

def main():
    # Configuración
    host_tcp = "localhost"
    puerto_tcp = 8080
    clave_publica_pem = cargar_clave_publica()
    url_opcua = "opc.tcp://localhost:4840"
    nodo_opcua = "ns=2;i=123"

    # Ejecutar diagnósticos OPC UA
    if not verificar_conexion_opcua(url_opcua):
        if not crear_nodo_opcua_si_no_existe(url_opcua, nodo_opcua):
            print("\n⚠️ No se pudo conectar al servidor OPC UA ni crear nodo. Verifica que el servidor OPC UA esté ejecutándose.")
            return

    if not verificar_nodo_opcua(url_opcua, nodo_opcua):
        if not crear_nodo_opcua_si_no_existe(url_opcua, nodo_opcua):
            print("\n⚠️ No se pudo verificar ni crear el nodo OPC UA. El sistema puede no funcionar correctamente.")
            return

    # Cargar clave pública
    clave_publica = serialization.load_pem_public_key(clave_publica_pem)

    # Crear socket TCP
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((host_tcp, puerto_tcp))
        s.listen(1)
        print(f"\nServidor Intermedio escuchando en {host_tcp}:{puerto_tcp}...")
        
        while True:
            try:
                conexion, direccion = s.accept()
                print(f"\nConexión entrante desde: {direccion}")
                
                with conexion:
                    # Recibir firma (256 bytes)
                    firma = conexion.recv(256)
                    if len(firma) != 256:
                        print("Error: Firma incompleta")
                        conexion.sendall(b"\x00")
                        continue
                    
                    # Recibir JSON
                    datos_recibidos = b""
                    while True:
                        chunk = conexion.recv(4096)
                        if not chunk:
                            break
                        datos_recibidos += chunk
                        try:
                            json.loads(datos_recibidos.decode('utf-8'))
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
                            # Enviar solo el valor de temperatura como ejemplo
                            cliente.get_node(nodo_opcua).set_value(datos["temperatura"])
                            print("→ Enviado a OPC UA")
                            conexion.sendall(b"\x01")
                        except Exception as opc_error:
                            print(f"Error OPC UA: {str(opc_error)}")
                            conexion.sendall(b"\x00")
                        finally:
                            try:
                                cliente.disconnect()
                            except:
                                pass

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