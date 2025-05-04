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
#define PIR_PIN 25  // Ustaw tutaj pin, do którego podłączony jest czujnik PIR

Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, -1);
Preferences preferences;

// Obiekty MQTT
WiFiClient espClient;
PubSubClient mqttClient(espClient);

const char* apName = "Salon_czujnik_ruchu";
const char* apPassword = "12345678";

int logic_clock = 0;

void reconnectMQTT() {
  while (!mqttClient.connected()) {
    Serial.print("Łączenie z brokerem MQTT...");
    if (mqttClient.connect("Salon_PIR")) {
      Serial.println(" połączono!");
      // Opcjonalnie: subskrypcja tematów, jeśli potrzebujesz
    } else {
      Serial.print("Błąd, rc=");
      Serial.print(mqttClient.state());
      Serial.println(" Próba ponownego połączenia za 5 sekund.");
      delay(5000);
    }
  }
}


void setup() {
  Serial.begin(9600);
  Serial.println();
  Serial.println("=== Start OLED + PIR test ===");

  // Ustawienie właściwych pinów I2C (SDA=GPIO21, SCL=GPIO22)
  Wire.begin(21, 22);

  // Inicjalizacja wyświetlacza OLED
  if (!display.begin(SSD1306_SWITCHCAPVCC, 0x3C)) {
    Serial.println("Błąd inicjalizacji SSD1306!");
    while(true) {}
  }
  
  // Konfiguracja pinu czujnika PIR jako wejście
  pinMode(PIR_PIN, INPUT_PULLDOWN);
  pinMode(23, OUTPUT);
  
  // Początkowa konfiguracja wyświetlacza
  display.clearDisplay();
  display.setTextSize(1);
  display.setTextColor(WHITE);
  display.setCursor(0, 0);

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
  int n = MDNS.queryService("_mqtt", "_tcp");
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
}

void loop() {
  if (!mqttClient.connected()) {
    reconnectMQTT();
  }
  mqttClient.loop();

  // Odczyt stanu czujnika PIR
  int pirState = digitalRead(PIR_PIN);
  
  // Wyczyść ekran przed aktualizacją informacji
  display.clearDisplay();
  display.setCursor(0, 0);
  
  // Sprawdzenie czy wykryto ruch i aktualizacja wyświetlacza oraz portu szeregowego
  if (pirState == HIGH) {
    logic_clock++;

    display.println("Ruch wykryty!");
    Serial.println("Ruch wykryty!");
    if(mqttClient.publish("salon/ruch/", String(logic_clock).c_str())) {
      Serial.println("Wysłano true do salon/ruch/");
    } else {
      Serial.println("Błąd wysyłania wiadomości MQTT");
    }
    if(logic_clock==1000)
      logic_clock = 0;
    digitalWrite(23, HIGH);
  } else {
    display.println("Brak ruchu.");
    Serial.println("Brak ruchu.");
    digitalWrite(23, LOW);
  }
  
  display.display();
  delay(500); // Krótka przerwa przed kolejnym odczytem
}
