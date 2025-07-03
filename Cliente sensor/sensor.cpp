#include <iostream>
#include <chrono>
#include <thread>
#include <cstring>
#include <sstream>
#include <cstdlib>
#include <ctime>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <unistd.h>
#include <nlohmann/json.hpp>

struct SensorPacket {
    int16_t id;
    int64_t timestamp;
    float temperatura;
    float presion;
    float humedad;
    uint32_t firma;
};

uint32_t generarFirma(const SensorPacket& packet) {
    std::hash<std::string> hasher;
    std::ostringstream oss;
    oss << packet.id << packet.timestamp << packet.temperatura << packet.presion << packet.humedad;
    return static_cast<uint32_t>(hasher(oss.str()));
}

float valorAleatorio(float min, float max) {
    return min + static_cast<float>(rand()) / (static_cast<float>(RAND_MAX / (max - min)));
}

int main() {
    srand(time(nullptr));

    int sock = socket(AF_INET, SOCK_STREAM, 0);
    if (sock < 0) {
        perror("Error al crear socket");
        return 1;
    }

    sockaddr_in serverAddr{};
    serverAddr.sin_family = AF_INET;
    serverAddr.sin_port = htons(8080); // Puerto del servidor intermedio
    inet_pton(AF_INET, "127.0.0.1", &serverAddr.sin_addr); // Cambia a IP del servidor real

    if (connect(sock, (sockaddr*)&serverAddr, sizeof(serverAddr)) < 0) {
        perror("Error al conectar al servidor");
        close(sock);
        return 1;
    }

    std::cout << "Conectado al servidor.\n";

    while (true) {
        // Generar datos
        int16_t id = 1;
        int64_t timestamp = std::chrono::duration_cast<std::chrono::seconds>(
            std::chrono::system_clock::now().time_since_epoch()).count();
        float temperatura = valorAleatorio(20.0, 100.0);
        float presion = valorAleatorio(950.0, 1050.0);
        float humedad = valorAleatorio(30.0, 100.0);

        // Crear el paquete para la firma
        SensorPacket packet{id, timestamp, temperatura, presion, humedad, 0};
        uint32_t firma_simulada = generarFirma(packet);

        // Crear JSON con los datos
        nlohmann::json j;
        j["id"] = id;
        j["timestamp"] = timestamp;
        j["temperatura"] = temperatura;
        j["presion"] = presion;
        j["humedad"] = humedad;

        std::string mensaje_json = j.dump();

        // Enviar [firma][datos]
        send(sock, &firma_simulada, sizeof(firma_simulada), 0);
        send(sock, mensaje_json.c_str(), mensaje_json.size(), 0);

        std::this_thread::sleep_for(std::chrono::seconds(1));
    }
    close(sock);
    return 0;
}
