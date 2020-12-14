#funkcja odbierająca dane z brokera
def sub_cb(topic, msg):
    print((topic, msg))
    
    global remote_MAC
    
    #jeżeli w subskrybowanym temacie pojawił się komunikat '1'
    if(msg == b'1'):
        led.value(1)
        time.sleep(0.1)
        led.value(0)
        time.sleep(0.1)
        led.value(1)
        time.sleep(0.1)
        led.value(0)
        time.sleep(0.1)
        led.value(1)
        time.sleep(0.1)
        led.value(0)
        time.sleep(0.1)
        send_magic_packet(remote_MAC)
        print('Wysłano rozkaz uruchomienia komputera.')
    else:        
        led.value(0)

#funkcja łącząca się z brokerem i subskrybująca wybrany temat
def connect_and_subscribe():
    global client_id, mqtt_server, topic_sub
    client = MQTTClient(client_id, mqtt_server, 1883, mqtt_user, mqtt_pass)
    client.set_callback(sub_cb)
    client.connect()
    client.subscribe(topic_sub)
    print('Połączono z brokerem MQTT: %s, Subskrybowany temat: %s ' % (mqtt_server, topic_sub))
    return client

#funkcja resetująca ESP32
def restart_and_reconnect():
    print('Błąd podczas łączenia z brokerem. Ponowne uruchamianie..')
    time.sleep(10)
    machine.reset()


try:
    client = connect_and_subscribe()
except OSError as e:
    restart_and_reconnect()

while True:
    try:
        #sprawdzenie czy nie ma nowych danych w subskrybowanym temacie
        client.check_msg()
        
        #wysłanie danych w celu podtrzymania połączenia co określony czas (message_interval = 5)
        if (time.time() - last_message) > message_interval:
            msg = b'connection hold'
            client.publish(topic_pub, msg)
            
            last_message = time.time()
            
    except OSError as e:
        restart_and_reconnect()

