Guía de Ejecución del Sistema IoT Industrial
===========================================

Requisitos Previos:
---------------------
- Sistema Operativo: WSL2 (Ubuntu 22.04) o Linux nativo
- Python: Versión 3.10 o superior
- C++: Compilador g++ (GCC 11.3.0+)
- Gestor de Paquetes: pip (Python) y apt (WSL/Linux)

Instalación de Dependencias:
-----------------------------

1. Instalar dependencias del sistema (WSL/Linux):
sudo apt update && sudo apt install -y python3 python3-pip g++ build-essential

2. Instalar módulos Python:
python3 -m venv venv
source venv/bin/activate
pip install fastapi uvicorn httpx cryptography python-opcua

3. Instalar biblioteca JSON para C++:
sudo apt install -y nlohmann-json3-dev

Ejecución del Sistema (4 Terminales):
---------------------------------------

Terminal 1: Servidor Final (API REST)
cd src/servidor_final/
uvicorn main:app --reload
Verificación: Abrir en navegador http://127.0.0.1:8000/docs

Terminal 2: Servidor Intermedio (Python)
cd src/
python3 servidor_intermedio.py
Verificación: Debe mostrar "Servidor Intermedio escuchando en localhost:8080..."

Terminal 3: Cliente Sensor (C++)
cd Cliente\ sensor/
g++ sensor.cpp -o sensor -I/usr/include/nlohmann -lssl -lcrypto && ./sensor
Verificación: Debe mostrar "Conectado al servidor. Enviando datos: Temp=25.5, Presión=1013.2..."

Terminal 4: Cliente de Consulta (Python)
cd src/
python3 cliente_consultas.py
Verificación: Mostrará datos cada 5 segundos: "[{"temperatura": 25.5, "presion": 1013.2, "humedad": 60.0}]"

Solución de Problemas Comunes:
-------------------------------

1. Error "ModuleNotFoundError":
pip install <módulo_faltante>

2. Cliente Sensor no envía datos:
- Verificar puerto del Servidor Intermedio (8080)
- Verificar archivo clave_publica.pem en Seguridad/

3. API no devuelve datos:
curl http://127.0.0.1:8000/mediciones

Notas Adicionales:
--------------------
Versiones Probadas:
- Python 3.10.12
- g++ 11.4.0
- FastAPI 0.95.2

Estructura del Proyecto:
Proyecto/
├── Seguridad/               # Claves PEM
├── src/                     # Código Python
│   ├── servidor_final/      # API REST
│   └── ...
└── Cliente sensor/          # Código C++

Documentación Adicional:
-------------------------
- FastAPI: https://fastapi.tiangolo.com
- Uvicorn: https://www.uvicorn.org
- nlohmann/json: https://github.com/nlohmann/json