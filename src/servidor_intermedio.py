import json
import socket
from pathlib import Path

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from opcua import Client

from database import crear_tabla, insertar_medicion


def cargar_clave_publica():
    # Buscar en varias ubicaciones posibles
    posibles_rutas = [
        Path(__file__).parent.parent / "Seguridad" / "clave_publica.pem",
        Path(__file__).parent / "Seguridad" / "clave_publica.pem",
        Path("Seguridad/clave_publica.pem"),
        Path("clave_publica.pem")
    ]
    
    for ruta_clave in posibles_rutas:
        if ruta_clave.exists():
            try:
                with open(ruta_clave, "rb") as f:
                    return f.read()
            except Exception as e:
                continue
            
    raise Exception(
        "No se encontró 'clave_publica.pem' en ninguna de las ubicaciones probadas.\n"
        "Solución: Copia el archivo PEM a una de estas rutas:\n" +
        "\n".join(str(p) for p in posibles_rutas)
    )

def verificar_conexion_opcua(url):
    """Verificar conexión OPC UA"""
    print("\n=== Verificando conexión OPC UA ===")
    client = Client(url)                  # Crea un cliente OPC UA con la URL proporcionada
    try:
        client.connect()
        print("Conexión OPC UA exitosa!")
        client.disconnect()
        return True
    except Exception as e:
        print(f"Error conectando a OPC UA: {e}")
        return False
    finally:
        try:
            client.disconnect()           # Asegura que el cliente se desconecte correctamente
        except:
            pass

def verificar_nodo_opcua(url, nodo):
    """Verificar nodo OPC UA"""
    print("\nVerificando nodo OPC UA")
    client = Client(url)
    try:
        client.connect()
        try:
            node = client.get_node(nodo)                                  # Un nodo en OPC UA es un objeto que representa un recurso o entidad en el servidor OPC UA.
            valor = node.get_value()                                      # El valor del nodo es el dato actual almacenado en ese nodo.
            print(f"Nodo encontrado. Valor actual: {valor}")
            return True
        except Exception as e:
            print(f"Error accediendo al nodo: {e}")
            return False
    except Exception as e:
        print(f"Error de conexión durante verificación de nodo: {e}")
        return False
    finally:
        try:
            client.disconnect()                                           # Asegura que el cliente se desconecte correctamente
        except:
            pass

def main():
    # Configuración del servidor intermedio
    host_tcp = "localhost" 
    puerto_tcp = 8080
    clave_publica_pem = cargar_clave_publica()
    url_opcua = "opc.tcp://localhost:4840"
    nodo_opcua = "ns=2;i=123"
    
    # Iniciar la base de datos
    crear_tabla()

    # Cargar clave pública
    clave_publica = serialization.load_pem_public_key(clave_publica_pem)  # serialization es un módulo de la biblioteca cryptography que permite convertir objetos a un formato que se puede almacenar o transmitir, y luego reconstruirlos a partir de ese formato.

    # Verificar conexión OPC UA una vez al inicio
    if not verificar_conexion_opcua(url_opcua):
        print("\nNo se pudo conectar al servidor OPC UA. Verifica que el servidor OPC UA esté ejecutándose.")
        return

    # Verificar nodo OPC UA una vez al inicio
    if not verificar_nodo_opcua(url_opcua, nodo_opcua):
        print("\nNo se pudo encontrar el nodo OPC UA. Verifica la configuración del servidor OPC UA.")
        return

    # Crear socket TCP
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:          # socket.socket(ipv4, TCP)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)           # setsockopt es una función que permite configurar opciones del socket. (nivel de socket, opción a configurar, valor de la opción)
        s.bind((host_tcp, puerto_tcp))                                    # bind asocia el socket a una dirección y puerto específicos. (dirección IP, puerto)
        s.listen(1)                                                       # listen pone el socket en modo de escucha para aceptar conexiones entrantes. (1 = número máximo de conexiones en cola)
        print(f"\nServidor Intermedio escuchando en {host_tcp}:{puerto_tcp}...")
        
        while True:
            try:
                conexion, direccion = s.accept()                          # socket para comunicación con el cliente, dirección del cliente = accept es una función que acepta una conexión entrante y devuelve un nuevo socket para la comunicación con el cliente y la dirección del cliente.
                print(f"\nConexión entrante desde: {direccion}")
                
                with conexion:
                    # Recibir firma (256 bytes)
                    firma = conexion.recv(256)                            # recv es una función que recibe datos del socket. (tamaño máximo de bytes a recibir)
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
                        # Verificar firma con logs detallados
                        try:
                            clave_publica.verify(
                                firma,
                                datos_recibidos,
                                padding.PKCS1v15(),
                                hashes.SHA256()
                            )
                            print("Firma verificada correctamente")
                            
                            datos = json.loads(datos_recibidos.decode('utf-8'))
                            print("Datos verificados:", datos)
                            
                            # Enviar a OPC UA
                            cliente = Client(url_opcua)
                            try:
                                cliente.connect()
                                # Enviar todos los valores
                                cliente.get_node("ns=2;i=123").set_value(datos["temperatura"])  # Temperatura
                                cliente.get_node("ns=2;i=124").set_value(datos["humedad"])      # Humedad
                                cliente.get_node("ns=2;i=125").set_value(datos["presion"])      # Presión
                                print("Datos enviados a OPC UA")
                                
                                # Guardar en base de datos
                                insertar_medicion(
                                    id_sensor=datos["id"],
                                    timestamp=datos["timestamp"],
                                    temperatura=datos["temperatura"],
                                    presion=datos["presion"],
                                    humedad=datos["humedad"]
                                )
                                
                                print("Datos insertados en SQLite")
                                
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
                            print(f"Error de verificación (detalle técnico): {str(e)}")
                            print(f"Tamaño firma recibida: {len(firma)} bytes")
                            print(f"Clave pública usada: {clave_publica.public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo)}")
                            conexion.sendall(b"\x00")
                            continue

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