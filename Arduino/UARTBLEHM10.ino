#include <SoftwareSerial.h>
int Rx = 10; //conexión al módulo
int Tx = 11;
SoftwareSerial moduloBtLE(Rx,Tx);

bool escribeNombre = true;
String NAME = "AT+NAMEBT05-" + String(0)+ String(1) + "\r\n";
//String NAME = "AT+NAMEBT05-" + String(1) + "\r\n";


void setup(){
  
  int baudiosArduino = 9600;
  // Serial USB
  Serial.begin(baudiosArduino);
  while (!Serial) {
    }// espera conexión
  Serial.println("\n USB <->PC, Listo..!!");

  //Puerto Serial Módulo Bluetooth
  int baudiosBtLE = 9600;
  moduloBtLE.begin(baudiosBtLE);
  //delay(100);
  //moduloBtLE.write("AT+VERSION\r\n");
  //delay(100);
  //Serial.write(moduloBtLE.read());
  //delay(100);
  moduloBtLE.write("AT+NAME\r\n"); 
  delay(100);
  Serial.write(moduloBtLE.read());
  delay(100);
  //moduloBtLE.write("AT+PIN\r\n");
  //delay(100);
  //Serial.write(moduloBtLE.read());
  //delay(100);
  //moduloBtLE.write("AT+ROLE\r\n");
  //delay(100);
  ///Serial.write(moduloBtLE.read());
  if (escribeNombre == true){
    Serial.println("\n Changing Name: ");
    char myNameCharArray[NAME.length() + 1]; // +1 for null terminator
    NAME.toCharArray(myNameCharArray, NAME.length() + 1); // Copy string to char array
// myCharArray now holds the string as a char array
    moduloBtLE.write(myNameCharArray);
    delay(100);
    Serial.write(moduloBtLE.read());
    moduloBtLE.write("AT+RESET\r\n");
    delay(2000);
    moduloBtLE.write("AT+NAME\r\n");
    delay(100);
    Serial.write(moduloBtLE.read());
  }
  
  Serial.println("Listo Bluetooth a Tablet/móvil");
}

void loop(){
  // recibe mensaje Bluetooth y envia por USB a PC
  if (moduloBtLE.available()){
    Serial.write(moduloBtLE.read());
    }
  // envia mensaje Serial-USB a Bluetooth
  if (Serial.available()){
    moduloBtLE.write(Serial.read());
    }
  }