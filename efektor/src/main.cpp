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

#define swiatlo_pin 18
#define pstryczek_pin 19

// Ustawienia dla trybu Access Point (nazwa i hasło portalu konfiguracji)
const char* apName = "przedpokoj_swiatlo";
const char* apPassword = "12345678";

// Globalne stany
bool localState = false;    // stan fizycznego przełącznika (zdebouncowany)
bool remoteState = false;   // stan otrzymany przez MQTT
bool lightState = false;    // ostateczny stan światła

// Dodatkowe zmienne sterujące
bool lockedOff = false;     // flaga, że po fizycznym wyłączeniu światło ma pozostać OFF

// Zmienne do debouncingu pstryczka
bool lastReading = false;         // ostatni surowy odczyt
bool debouncedLocalState = false; // zdebouncowany stan
unsigned long lastDebounceTime = 0;
const unsigned long debounceDelay = 50;  // opóźnienie debouncingu (ms)

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
  if (strcmp(topic, "przedpokoj/swiatlo/") == 0) {
    if(message=="true"){
      remoteState = true;
      display.clearDisplay();
      display.setCursor(0, 0);
      display.println("true");
    }
    else{
      remoteState = false;
      display.clearDisplay();
      display.setCursor(0, 0);
      display.println("false");
    }
  }
}

void reconnectMQTT() {
  // Próba ponownego połączenia, dopóki nie uda się połączyć
  while (!mqttClient.connected()) {
    Serial.print("Attempting MQTT connection...");
    if (mqttClient.connect("ESP32-przedpokoj/swiatlo/")) {
      Serial.println(" connected");
      // Subskrybujemy topic "futryny/przedpokoj/"
      mqttClient.subscribe("przedpokoj/swiatlo/", 1);
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
  Serial.println("=== Start swiatlo przedpokoj ===");

  // Ustawienie pinów I2C (SDA=GPIO21, SCL=GPIO22)
  Wire.begin(21, 22);
  pinMode(swiatlo_pin, OUTPUT);
  pinMode(pstryczek_pin, INPUT_PULLDOWN);
  digitalWrite(swiatlo_pin, LOW);

  // Inicjalizacja OLED
  if (!display.begin(SSD1306_SWITCHCAPVCC, 0x3C)) {
    Serial.println("Błąd inicjalizacji OLED!");
    while(true) {}
  }
  
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
  IPAddress fallback(192, 168, 1, 150);   // Domyślny adres fallback
  IPAddress foundBroker;
  bool foundValid = false;

  if (n > 0) {
    // Sprawdź wszystkie wyszukane serwisy
    for (int i = 0; i < n; i++) {
      IPAddress candidate = MDNS.IP(i);
      if (candidate != IPAddress(192,168,0,1)) {
        // Wybieramy kandydata o ile nie jest 192.168.0.1
        foundBroker = candidate;
        foundValid = true;
        Serial.print("Znaleziono brokera MQTT przez mDNS: ");
        Serial.println(foundBroker);
        break; 
      }
    }
  }

  if (!foundValid) {
    // Jeśli nic nie znaleźliśmy lub wszystko było 192.168.0.1
    Serial.println("Brak prawidłowego wyniku z mDNS, używam fallback.");
    foundBroker = fallback;
  }

  mqttClient.setServer(foundBroker, 1883);
  mqttClient.setCallback(mqttCallback);
}

void loop() {
  if (!mqttClient.connected()) {
    reconnectMQTT();
  }
  mqttClient.loop();
  
  // Debouncing fizycznego przełącznika (pstryczka)
  bool currentReading = digitalRead(pstryczek_pin);
  if (currentReading != lastReading) {
    lastDebounceTime = millis();
  }
  if ((millis() - lastDebounceTime) > debounceDelay) {
    // Jeśli stan utrzymuje się przez debounceDelay, uznajemy go za stabilny
    debouncedLocalState = currentReading;
  }
  lastReading = currentReading;
  
  // Ustalanie stanu lokalnego na podstawie zdebouncowanego odczytu
  bool prevLocalState = localState;
  localState = debouncedLocalState;  // HIGH oznacza fizyczne włączenie

  // Mechanizm blokady: 
  // Jeśli lokalny przełącznik przechodzi z ON do OFF, ustawiamy lockedOff = true
  if (prevLocalState == true && localState == false) {
    lockedOff = true;
  }
  // Jeśli pojawi się nowa aktywacja (lokalna lub nowy sygnał zdalny), odblokowujemy
  if (localState == true || (remoteState == true && remoteState != prevLocalState)) {
    lockedOff = false;
  }

  // Priorytet – fizyczny przełącznik ma pierwszeństwo
  if (localState == true) {
    lightState = true;
  } else if (lockedOff == true) {
    lightState = false;
  } else {
    lightState = remoteState;
  }
  
  digitalWrite(swiatlo_pin, lightState ? HIGH : LOW);
  
  
  display.clearDisplay();
  display.setCursor(0, 0);
  display.print("swiatlo_pin: ");
  display.println(digitalRead(swiatlo_pin) == LOW ? "LOW" : "HIGH");
  display.print("pstryczek_pin: ");
  display.println(digitalRead(pstryczek_pin) == LOW ? "LOW" : "HIGH");
  display.display();

  
  delay(50);  // Pauza przed kolejnym odczytem
}