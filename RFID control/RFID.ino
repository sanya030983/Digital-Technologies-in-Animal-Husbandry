#include <SPI.h>
#include <MFRC522.h>
#include <Servo.h>

#define RST_PIN   9
#define SS_PIN    10
#define SERVO_PIN 6
#define BUZZER_PIN 5

MFRC522 rfid(SS_PIN, RST_PIN);
Servo gateServo;

void setup() {
  Serial.begin(9600);
  SPI.begin();
  rfid.PCD_Init();
  gateServo.attach(SERVO_PIN);
  gateServo.write(0);                // исходное положение (закрыто)
  pinMode(BUZZER_PIN, OUTPUT);
  digitalWrite(BUZZER_PIN, LOW);
  Serial.println("RFID reader ready");
}

void loop() {
  // Обработка команд с ПК
  if (Serial.available()) {
    char cmd = Serial.read();
    if (cmd == 'O') {                 // открыть ворота
      openGate();
    } else if (cmd == 'D') {          // запрет доступа (два сигнала)
      denyAccess();
    } else if (cmd == 'A') {          // подтверждение добавления
      ackAdd();
    }
  }

  // Поиск новой RFID-метки
  if (!rfid.PICC_IsNewCardPresent() || !rfid.PICC_ReadCardSerial()) {
    return;
  }

  // Формируем строку UID в формате HEX с двоеточиями
  String uidStr = "";
  for (byte i = 0; i < rfid.uid.size; i++) {
    if (rfid.uid.uidByte[i] < 0x10) uidStr += "0";
    uidStr += String(rfid.uid.uidByte[i], HEX);
    if (i < rfid.uid.size - 1) uidStr += ":";
  }
  uidStr.toUpperCase();

  // Отправляем UID на ПК
  Serial.println("UID:" + uidStr);

  rfid.PICC_HaltA();   // завершаем сессию с меткой
}

// Открытие ворот (поворот на 90°, задержка, возврат) + длинный сигнал
void openGate() {
  digitalWrite(BUZZER_PIN, HIGH);
  delay(500);
  digitalWrite(BUZZER_PIN, LOW);
  gateServo.write(90);
  delay(3000);
  gateServo.write(0);
}

// Два коротких сигнала (доступ запрещён)
void denyAccess() {
  for (int i = 0; i < 2; i++) {
    digitalWrite(BUZZER_PIN, HIGH);
    delay(200);
    digitalWrite(BUZZER_PIN, LOW);
    delay(200);
  }
}

// Короткий двойной сигнал (подтверждение добавления)
void ackAdd() {
  digitalWrite(BUZZER_PIN, HIGH);
  delay(200);
  digitalWrite(BUZZER_PIN, LOW);
  delay(50);
  digitalWrite(BUZZER_PIN, HIGH);
  delay(200);
  digitalWrite(BUZZER_PIN, LOW);
}