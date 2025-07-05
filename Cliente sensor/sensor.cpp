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
#include <openssl/err.h>
#include <openssl/evp.h>
#include <sys/stat.h>
#include <openssl/pem.h>

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

// Cargar clave privada con la nueva API
EVP_PKEY* cargarClavePrivada(const char* filename) {
    FILE* fp = fopen(filename, "r");
    if (!fp) {
        std::cerr << "Error al abrir archivo de clave: " << filename << "\n";
        return nullptr;
    }
    
    EVP_PKEY* pkey = PEM_read_PrivateKey(fp, nullptr, nullptr, nullptr);
    fclose(fp);
    
    if (!pkey) {
        std::cerr << "Error al leer clave privada (¿formato incorrecto?)\n";
        ERR_print_errors_fp(stderr);  // Muestra detalles del error de OpenSSL
    }
    
    return pkey;
}

// Firmar mensaje con la nueva API
int firmarMensaje(EVP_PKEY* pkey, const std::string& mensaje, unsigned char* firma, size_t* firma_len) {
    EVP_MD_CTX* ctx = EVP_MD_CTX_new();
    if (!ctx) return 0;

    // Inicializar operación de firma
    if (EVP_DigestSignInit(ctx, nullptr, EVP_sha256(), nullptr, pkey) != 1) {
        EVP_MD_CTX_free(ctx);
        return 0;
    }

    // Actualizar con los datos a firmar
    if (EVP_DigestSignUpdate(ctx, mensaje.c_str(), mensaje.size()) != 1) {
        EVP_MD_CTX_free(ctx);
        return 0;
    }

    // Obtener tamaño de la firma
    if (EVP_DigestSignFinal(ctx, nullptr, firma_len) != 1) {
        EVP_MD_CTX_free(ctx);
        return 0;
    }

    // Realizar la firma
    if (EVP_DigestSignFinal(ctx, firma, firma_len) != 1) {
        EVP_MD_CTX_free(ctx);
        return 0;
    }

    EVP_MD_CTX_free(ctx);
    return 1;
}

int main() {
    srand(time(nullptr));

    // Verificar existencia de archivo de clave privada
    struct stat buffer;
    if (stat("../Seguridad/clave_privada_rsa.pem", &buffer) != 0) {
        std::cerr << "Archivo de clave privada NO encontrado en ../Seguridad/clave_privada_rsa.pem\n";
        return 1;
    }

    // Cargar clave privada con la nueva API
    EVP_PKEY* pkey = cargarClavePrivada("../Seguridad/clave_privada_rsa.pem");
    if (!pkey) {
        std::cerr << "No se pudo cargar la clave privada.\n";
        return 1;
    }

    int sock = socket(AF_INET, SOCK_STREAM, 0);
    if (sock < 0) {
        perror("Error al crear socket");
        EVP_PKEY_free(pkey);
        return 1;
    }

    sockaddr_in serverAddr{};
    serverAddr.sin_family = AF_INET;
    serverAddr.sin_port = htons(8080);
    inet_pton(AF_INET, "127.0.0.1", &serverAddr.sin_addr);

    if (connect(sock, (sockaddr*)&serverAddr, sizeof(serverAddr)) < 0) {
        perror("Error al conectar al servidor");
        close(sock);
        EVP_PKEY_free(pkey);
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

        // Crear JSON con los datos
        nlohmann::json j;
        j["id"] = id;
        j["timestamp"] = timestamp;
        j["temperatura"] = temperatura;
        j["presion"] = presion;
        j["humedad"] = humedad;
        std::string mensaje_json = j.dump();

        // Chequeo de tamaño del JSON
        if (mensaje_json.size() > 4096 - 256) {
            std::cerr << "Error: JSON demasiado grande\n";
            break;
        }

        // Firmar el mensaje JSON
        unsigned char firma[256];
        size_t firma_len = sizeof(firma);
        if (!firmarMensaje(pkey, mensaje_json, firma, &firma_len)) {
            std::cerr << "Error al firmar el mensaje.\n";
            break;
        }

        // --- DEPURACIÓN ADICIONAL ---
        // Imprimir los primeros bytes de la firma generada (hex)
        std::cout << "Firma generada (hex): ";
        for(int i = 0; i < 20 && i < firma_len; i++) {
            printf("%02x", firma[i]);
        }
        std::cout << "... (longitud: " << firma_len << " bytes)\n";

        // Imprimir el JSON que se está firmando
        std::cout << "JSON que se firmó: " << mensaje_json << "\n";
        // ---------------------------

        // Enviar [firma][datos]
        ssize_t sent_firma = send(sock, firma, firma_len, 0);
        if (sent_firma != (ssize_t)firma_len) {
            std::cerr << "Error al enviar la firma o conexión cerrada.\n";
            break;
        }
        ssize_t sent_json = send(sock, mensaje_json.c_str(), mensaje_json.size(), 0);
        if (sent_json != (ssize_t)mensaje_json.size()) {
            std::cerr << "Error al enviar el JSON o conexión cerrada.\n";
            break;
        }
        std::cout << "Enviando datos - Temp: " << temperatura
            << "°C, Presión: " << presion
            << " hPa, Humedad: " << humedad << "%\n";

        char respuesta;
        int bytes_recibidos = recv(sock, &respuesta, 1, 0);
        if (bytes_recibidos <= 0) {
            std::cerr << "Error en confirmación: ";
            if (bytes_recibidos == 0) {
                std::cerr << "Conexión cerrada por el servidor\n";
            } else {
                perror("recv()");
            }
            close(sock);
            // Aquí agregar lógica para reconectar
            break;
        }

        // Chequeo de confirmación del servidor
        if (respuesta == '\x01') {
            std::cout << "Confirmación recibida. Envío exitoso.\n";
        } else {
            std::cerr << "El servidor reportó un error al procesar\n";
            close(sock);
            // Aquí agregar lógica para reconectar
            break;
        }

        std::this_thread::sleep_for(std::chrono::seconds(1));
    }
    close(sock);
    EVP_PKEY_free(pkey);
    return 0;
}