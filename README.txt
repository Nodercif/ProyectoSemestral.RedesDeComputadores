CÓMO EJECUTAR TODO EL PROYECTO:

// En la dirección correspondiente al src del repositorio
1. Abrir 4 terminales
2. Terminal 1, ejecutar Servidor Final (Python) con "uvicorn main:app --reload"
	- NOTA: En esta terminal, se debe ingresar primero al directorio "servidor_final"
3. Terminal 2, ejecutar Servidor Intermedio (Python) con "python servidor_intermedio.py"
4. Terminal 3, ejecutar Cliente Sensor (C++) con "g++ sensor.cpp -o sensor -I/usr/include/nlohmann && ./sensor"
5. Terminal 4, ejecutar Cliente de Consulta (Python) con "python cliente_consulta.py"