/*
 * SENTINELA ORBITAL - Firmware da estacao de sensores de solo (ESP32)
 * -------------------------------------------------------------------
 * Le sensores fisicos e envia JSON via HTTP POST para a API/Lambda na
 * nuvem. Mesma logica de risco do simulador Python (sensor_simulator.py),
 * permitindo trocar a simulacao por hardware real sem mudar o backend.
 *
 * Hardware:
 *   - ESP32 DevKit v1
 *   - DHT22  -> temperatura/umidade do ar      (GPIO 4)
 *   - Sensor capacitivo de umidade do solo     (GPIO 34 / ADC)
 *   - MQ-2   -> fumaca/gases                    (GPIO 35 / ADC)
 *
 * Bibliotecas (Arduino IDE / Library Manager):
 *   - DHT sensor library (Adafruit)
 *   - ArduinoJson
 */
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <DHT.h>

#define DHTPIN   4
#define DHTTYPE  DHT22
#define SOLO_PIN 34
#define MQ2_PIN  35

const char* WIFI_SSID = "SUA_REDE";
const char* WIFI_PASS = "SUA_SENHA";
// Endpoint da API Gateway -> Lambda (ou servidor local de testes)
const char* API_URL   = "https://SEU-ENDPOINT.execute-api.us-east-1.amazonaws.com/sensor";
const char* ESTACAO   = "Estacao Floresta-01 (Amazonia Legal)";

DHT dht(DHTPIN, DHTTYPE);

float calcularRisco(float tempAr, float umidAr, float tempSolo,
                    float umidSolo, float fumacaPpm) {
  float fTemp     = constrain((tempAr - 20.0) / 25.0, 0.0, 1.0);
  float fSecaAr   = constrain((60.0 - umidAr) / 60.0, 0.0, 1.0);
  float fSecaSolo = constrain((50.0 - umidSolo) / 50.0, 0.0, 1.0);
  float fFumaca   = constrain(fumacaPpm / 800.0, 0.0, 1.0);
  float fTempSolo = constrain((tempSolo - 18.0) / 30.0, 0.0, 1.0);
  float risco = (0.28 * fTemp + 0.22 * fSecaAr + 0.18 * fSecaSolo +
                 0.24 * fFumaca + 0.08 * fTempSolo) * 100.0;
  return risco;
}

String classificarNivel(float risco) {
  if (risco < 25) return "BAIXO";
  if (risco < 50) return "MODERADO";
  if (risco < 75) return "ALTO";
  return "CRITICO";
}

void conectarWifi() {
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  Serial.print("Conectando WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println(" OK");
}

void setup() {
  Serial.begin(115200);
  dht.begin();
  conectarWifi();
}

void loop() {
  float tempAr = dht.readTemperature();
  float umidAr = dht.readHumidity();

  // Sensores analogicos (ADC 12 bits: 0-4095). Conversoes aproximadas.
  int soloRaw = analogRead(SOLO_PIN);
  float umidSolo = map(soloRaw, 0, 4095, 100, 0);   // mais seco -> menor %
  int mq2Raw = analogRead(MQ2_PIN);
  float fumacaPpm = map(mq2Raw, 0, 4095, 0, 1000);
  float tempSolo = tempAr - 3.0;                     // estimativa simples

  float risco = calcularRisco(tempAr, umidAr, tempSolo, umidSolo, fumacaPpm);
  String nivel = classificarNivel(risco);

  StaticJsonDocument<256> doc;
  doc["estacao"]      = ESTACAO;
  doc["temp_ar"]      = tempAr;
  doc["umid_ar"]      = umidAr;
  doc["temp_solo"]    = tempSolo;
  doc["umid_solo"]    = umidSolo;
  doc["fumaca_ppm"]   = fumacaPpm;
  doc["risco_sensor"] = risco;
  doc["nivel"]        = nivel;

  String payload;
  serializeJson(doc, payload);
  Serial.println(payload);

  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    http.begin(API_URL);
    http.addHeader("Content-Type", "application/json");
    int code = http.POST(payload);
    Serial.printf("HTTP %d\n", code);
    http.end();
  }

  delay(30000);  // envia a cada 30 s
}
