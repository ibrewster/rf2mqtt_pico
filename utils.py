import uasyncio as asyncio

import machine
import network
import rp2

from mqtt import MQTTClient
from shelve import ShelveFile
from config import SETTINGS_FILE


SETTINGS={
    'debug':False,
    'APMODE':False
}

def post_button_mqtt(button):
    with ShelveFile(SETTINGS_FILE) as settings:
        mqtt_channel=settings.get('mqtt_channel','RF2MQTT/remote/{button}')
    topic=mqtt_channel.format(button=button)
    message='ON'
    
    return publish_mqtt(topic, message)

def publish_mqtt(topic, message, retain=False):
    with ShelveFile(SETTINGS_FILE) as settings:
        mqtt_broker=settings.get('mqtt_broker')
        mqtt_user=settings.get('mqtt_user') or None # Replaces empty string with None
        mqtt_password=settings.get('mqtt_password') or None
        
    if mqtt_broker is None:
        print("MQTT Broker not set!")
        return False
    
    mqtt_client=MQTTClient("RF2MQTT_PICO",mqtt_broker,user=mqtt_user, password=mqtt_password)
    mqtt_client.connect()
    mqtt_client.publish(topic, message, retain=retain)
    mqtt_client.disconnect()
    
    return True

async def connect_wifi(watcher):
    print("Connecting to WLAN")
    watcher.BUTTON_LEDS[1].on()
    rp2.country('US')
    
    with ShelveFile(SETTINGS_FILE) as settings:
        ssid=settings.get('wifi_ssid')
        password=settings.get('wifi_password')
        
    if ssid is None:
        wlan = network.WLAN(network.AP_IF)
        wlan.config(essid='RF2MQTT_CONFIG', password='rf2mqtt_pass')
        SETTINGS['APMODE']=True
    else:
        wlan = network.WLAN(network.STA_IF)
        
    wlan.active(True)
    watcher.BUTTON_LEDS[2].on()

    
    # Disable low power mode
    wlan.config(pm = network.WLAN.PM_NONE)
    
    if ssid is None:
        wlan.ifconfig(('192.168.10.1', '255.255.255.0','192.168.10.1','8.8.8.8'))
    else:
        wlan.connect(ssid, password)
    
    watcher.BUTTON_LEDS[3].on()
    watcher.BUTTON_LEDS[4].blink(n=None)
    
    max_wait=30
    while max_wait>0:
        if wlan.status()<0 or wlan.status()>=3:
            break
        max_wait -=1
        print("Waiting for connection...")
        await asyncio.sleep(1)
    if wlan.status()!=3:
        print("Unable to connect. Resetting...")
        watcher.status_red.on()
        await asyncio.sleep(1)
        watcher.status_red.off()
        machine.reset()
    else:
        print("connected")
        status=wlan.ifconfig()
        print('ip=' + status[0])

    for LED in watcher.BUTTON_LEDS[1:5]:
        LED.off()
        
    return wlan

async def check_wifi(wlan,watcher):
    while True:
        if not wlan.isconnected():
            # If we lost WiFi, try to reconnect once. If that fails,
            # The connect function will do a full reset, repeating
            # Until it can connect
            watcher.status_red.on()
            watcher.power_led.blink(n=None)
            wlan.disconnect()
            await connect_wifi(watcher)
            watcher.power_led.on()
            watcher.status_green.blink(on_time=1/4, off_time=1/4,n=4)
        await asyncio.sleep(15)
