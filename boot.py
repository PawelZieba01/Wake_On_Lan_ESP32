import time
import ubinascii
import machine
import micropython

import network
from wakeonlan import send_magic_packet
from umqttsimple import MQTTClient
####################################
try:
    import usocket as socket
except:
    import socket
  
from time import sleep
from machine import Pin

import json
####################################
import esp
esp.osdebug(None)
import gc
gc.collect()

#inicjalizacja pinu LED
led = Pin(2, Pin.OUT)

#inicjalizacja pinu CONFIG
cfn_pin = Pin(4, Pin.IN, Pin.PULL_UP)

sleep(2)

#wygenerowanie id clienta
client_id = ubinascii.hexlify(machine.unique_id())

######################################### TRYB KONFIGURACJI URZĄDZENIA #########################################
#jeżeli pin D4 zwarty do GND, uruchom tryb konfiguracji urządzenia
if cfn_pin.value() == 0:
    print('Uruchomiono tryb konfiguracji urządzenia')
    
    #nazwa i hasło do access pointa
    APssid = 'ESP_WakeOnLan'
    APpassword = ''

    ap = network.WLAN(network.AP_IF)
    ap.active(True)

    #konfiguracja punktu dostęowego
    ap.ifconfig(('192.168.1.1', '255.255.255.0', '192.168.1.1', '8.8.8.8'))
    ap.config(essid = APssid, password = APpassword)



    #oczekiwanie na podłączenie urządzenia
    while ap.isconnected() == False:
        print('Oczekiwanie na połączenie')
        led.value(1)
        sleep(1)
        
    print('Podłączono urządzenie')
    print(ap.ifconfig())
    led.value(0)
    sleep(0.3)
    led.value(1)
    sleep(0.3)
    led.value(0)
    sleep(0.3)
    led.value(1)
    sleep(0.3)
    led.value(0)
    sleep(0.3)
    led.value(1)

    #konfiguracja gniazda
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('', 80))
    s.listen(5)



    while True:
        #jeżeli podłączono urządzenie
        if ap.isconnected():
            
            #odebranie połączenia od clienta
            conn, addr = s.accept()
            print('Połączono z: %s \n' % str(addr))
            
            #odebranie treści wiadomości i odesłanie potwierdzenia http
            request = conn.recv(1024)
            conn.sendall('HTTP/1.1 200 OK\nConnection: close\nServer: ESPWakeOnLan\nContent-Type: text/html\n\n')
            
            #print('Content = %s' % str(request))
            
            #jeżeli przysłano dane konfiguracyjne
            if request.find(b'conf') > 0:
                #znajdź dane json w wiadomości
                i = request.find(b'\r\n\r\n{')
                
                #jeżeli znaleziono dane json
                if i > 0:
                    #pobierz dane json do zmiennej
                    config_data = str(request[i+4:], 'utf-8')
                    print('')
                    print('odebrane dane JSON')
                    print(config_data)
                    
                    #otwórz/utwórz plik 'conf.txt' i zapisz w nim dane json
                    f = open('config.txt', 'w')
                    f.write("Plik konfiguracyjy dla ESP32\n" + config_data)
                    f.close()
                    
                    #odeślij odpowiedź w formacie json że wszystko jest OK
                    resp = json.dumps({'SrvResp': 'OK'})
                    print('')
                    print('wysłane dane JSON')
                    print(resp)
                    conn.send(resp)
            
            #jeżeli client łączy się pierwszy raz - rządanie strony głównej
            else:
                #odeślij stronę html z pliku 'index.html'
                with open('index.html', 'r') as html:
                    conn.send(html.read())
            #zamknij połączenie
            conn.close()
        
        #jeżeli nie podłączono urządzenia
        else:
            print('Oczekiwanie na połączenie')
            sleep(1)
################################################################################################################





#pobranie konfiguracji urządzenia z pliku 'config.txt'
f = open('config.txt', 'r')
conf_json = f.readlines()
f.close()

print(conf_json[1])

#parsowanie danych konfiguracyjnych w formacie json
parsed = json.loads(conf_json[1])

#adres MAC urządzenia, które ma zostać obudzone
remote_MAC = parsed['RemoteMAC']
#Konfiguracja MQTT 
mqtt_server = parsed['MQTTSrv']                              #adres serwera MQTT (broker)

last_message = 0
message_interval = 5            #czas pomiędzy kolejnymi publikacjami danych do podtrzymania połączenia z brokerem

#Konfiguracja danych do MQTT
ssid = parsed['WiFissid']                                    #nazwa sieci WiFi
password = parsed['WiFipass']                                #hasło do sieci WiFi
mqtt_user = parsed['MQTTUserName']                           #nazwa użytkownika na serwerze MQTT
mqtt_pass = parsed['MQTTUserPass']                           #hasło użytkownika na serwerze MQTT
topic_sub = parsed['MQTTSubTopic'].encode('utf-8')           #subskrybowany temat
topic_pub = parsed['MQTTSubTopic'].encode('utf-8')           #temat do publikacji danych


#Konfiguracja WiFi
station = network.WLAN(network.STA_IF)
station.active(True)
station.connect(ssid, password)

#czekaj na połączenie z siecią 
while station.isconnected() == False:
    pass

print('Połączono z siecią WiFi.')
print(station.ifconfig())

led.value(1)
time.sleep(0.3)
led.value(0)
time.sleep(0.3)
led.value(1)
time.sleep(0.3)
led.value(0)