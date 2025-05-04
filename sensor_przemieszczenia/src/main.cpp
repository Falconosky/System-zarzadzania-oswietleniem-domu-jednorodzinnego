#include <Arduino.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include <WiFi.h>
#include <WiFiManager.h>
#include <Preferences.h>
#include <PubSubClient.h>
#include <ESPmDNS.h>

#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64

Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, -1);
Preferences preferences;

// Definicje pinów czujnika HC-SR04
#define TRIG_PIN 33
#define ECHO_PIN 32

// Ustawienia dla trybu Access Point (nazwa i hasło portalu konfiguracji)
const char* apName = "Salon_czujnik_futryna";
const char* apPassword = "12345678";

bool test = false;
bool ktosPrzeszedl = false;

float futryna_dystans = 0;
float tolerancja = 5;

// Obiekty MQTT
WiFiClient espClient;
PubSubClient mqttClient(espClient);

void mqttCallback(char* topic, byte* payload, unsigned int length) {
  Serial.print("Message arrived [");
  Serial.print(topic);
  Serial.print("] ");
  String message;
  for (unsigned int i = 0; i < length; i++) {
    message += (char)payload[i];
  }
  Serial.println(message);
  
  // Jeśli wiadomość pochodzi z topicu "futryny/przedpokoj/"
  if (strcmp(topic, "futryny/salon/") == 0) {
    futryna_dystans = 0;
    float newTolerance = message.toFloat();
    if(newTolerance > 0) { // Aktualizujemy tolerancję tylko, gdy wartość jest większa od 0
      tolerancja = newTolerance;
      Serial.print("Zmieniono tolerancje: ");
      Serial.println(tolerancja);
    }
  }
}

void reconnectMQTT() {
  // Próba ponownego połączenia, dopóki nie uda się połączyć
  while (!mqttClient.connected()) {
    Serial.print("Attempting MQTT connection...");
    if (mqttClient.connect("ESP32Client")) {
      Serial.println(" connected");
      // Subskrybujemy topic "futryny/salon/"
      mqttClient.subscribe("futryny/salon/");
    } else {
      Serial.print(" failed, rc=");
      Serial.print(mqttClient.state());
      Serial.println(" try again in 5 seconds");
      delay(5000);
    }
  }
}

void setup() {
  Serial.begin(9600);
  Serial.println();
  Serial.println("=== Start OLED i czujnika HC-SR04 ===");

  // Ustawienie pinów I2C (SDA=GPIO21, SCL=GPIO22)
  Wire.begin(21, 22);

  // Inicjalizacja OLED
  if (!display.begin(SSD1306_SWITCHCAPVCC, 0x3C)) {
    Serial.println("Błąd inicjalizacji OLED!");
    while(true) {}
  }
  
  display.clearDisplay();
  display.setTextSize(1);
  display.setTextColor(WHITE);
  
  preferences.begin("wifi", false);

  String storedSSID = preferences.getString("ssid", "");
  String storedPassword = preferences.getString("pass", "");

  WiFiManager wifiManager;

  if (storedSSID != "" && storedPassword != "") {
    Serial.println("Próba połączenia z zapisanymi danymi...");
    WiFi.begin(storedSSID.c_str(), storedPassword.c_str());
    if (WiFi.waitForConnectResult(15000) != WL_CONNECTED) {
      Serial.println("Nie udało się połączyć z zapisanymi danymi. Uruchamiam konfigurację...");
      if (!wifiManager.autoConnect(apName, apPassword)) {
        Serial.println("Nie udało się skonfigurować WiFi. Restartowanie...");
        delay(3000);
        ESP.restart();
      }
    }
  } else {
    if (!wifiManager.autoConnect(apName, apPassword)) {
      Serial.println("Nie udało się skonfigurować WiFi. Restartowanie...");
      delay(3000);
      ESP.restart();
    }
  }

  preferences.putString("ssid", WiFi.SSID());
  preferences.putString("password", WiFi.psk());

  Serial.println("Połączono z WiFi!");
  Serial.print("Adres IP: ");
  Serial.println(WiFi.localIP());

  preferences.end();

   // Wyszukiwanie brokera MQTT przy użyciu mDNS
   if (!MDNS.begin("esp32")) {
    Serial.println("Błąd inicjalizacji MDNS");
  }
  int n = MDNS.queryService("mqtt", "tcp");
  IPAddress brokerIP;
  if(n == 0) {
    Serial.println("Nie znaleziono brokera MQTT przez MDNS. Używam domyślnego adresu 192.168.1.150");
    brokerIP = IPAddress(192, 168, 1, 150);  // Zmień ten adres na odpowiedni fallback
  } else {
    brokerIP = MDNS.IP(0);
    Serial.print("Znaleziono brokera MQTT: ");
    Serial.println(brokerIP);
  }
  mqttClient.setServer(brokerIP, 1883);
  mqttClient.setCallback(mqttCallback);

  // Konfiguracja pinów czujnika HC-SR04
  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);
}

void loop() {
  if (!mqttClient.connected()) {
    reconnectMQTT();
  }
  mqttClient.loop();

  long duration;
  float distance;
  bool ruch = false;
  
  // Wygeneruj impuls na czujniku HC-SR04
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(2);
  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);
  
  // Odczyt impulsu z pinu ECHO
  duration = pulseIn(ECHO_PIN, HIGH);
  
  // Oblicz odległość w centymetrach:
  // 0.0343 [cm/us] to prędkość dźwięku (w powietrzu), dzielimy przez 2 bo impuls przebywa drogę tam i z powrotem.
  distance = (duration * 0.0343) / 2;

  if(futryna_dystans==0)
    futryna_dystans = distance;
  else if (abs(futryna_dystans - distance) > tolerancja && !ktosPrzeszedl)
  {
    ruch = true;
    ktosPrzeszedl = true;
    // Publikujemy informację "true" na topicu "/salon/futryna"
    // Uwaga: PubSubClient nie obsługuje QoS 2, więc wiadomość zostanie wysłana z domyślnym QoS (0 lub 1).
    if(mqttClient.publish("salon/futryna/", "true")) {
      Serial.println("Wysłano true do salon/futryna");
    } else {
      Serial.println("Błąd wysyłania wiadomości MQTT");
    }
  }
  else if (abs(futryna_dystans - distance) < tolerancja && ktosPrzeszedl)
    ktosPrzeszedl = false;
  // Aktualizacja wyświetlacza OLED
  display.clearDisplay();
  display.setCursor(0, 0);
  display.println("Odleglosc:");
  display.print(distance);
  display.println(" cm");
  display.print("Test: ");
  display.println(test ? "True" : "False");
  display.print("Ruch: ");
  display.println(ruch ? "True" : "False");
  display.println();
  display.print("Futryna: ");
  display.println(futryna_dystans);
  display.print("Tolerancja: ");
  display.println(tolerancja);
  display.display();

  // Wypisanie wyniku w monitorze szeregowym
  Serial.print("Odleglosc: ");
  Serial.print(distance);
  Serial.println(" cm");
  
  delay(500);  // Pauza przed kolejnym odczytem
}