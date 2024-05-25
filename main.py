print("Execution start")
import network
import os
import time
import rp2

import uasyncio as asyncio
from machine import Timer, Pin, reset

import web

from rf import RFDevice
from mqtt import MQTTClient
from orchestrator import Orchestrator
from shelve import ShelveFile
from config import SETTINGS_FILE

AP_MODE=False

async def connect_wifi(watcher):
    global AP_MODE
    print("Connecting to WLAN")
    rp2.country('US')
    
    with ShelveFile(SETTINGS_FILE) as settings:
        ssid=settings.get('wifi_ssid')
        password=settings.get('wifi_password')
        
    if ssid is None:
        wlan = network.WLAN(network.AP_IF)
        wlan.config(essid='RF2MQTT_CONFIG', password='rf2mqtt_pass')
        AP_MODE=True
    else:
        wlan = network.WLAN(network.STA_IF)
    
        
    wlan.active(True)
    
    # Disable low power mode
    wlan.config(pm = network.WLAN.PM_NONE)
    
    if ssid is None:
        wlan.ifconfig(('192.168.10.1', '255.255.255.0','192.168.10.1','8.8.8.8'))
    else:
        wlan.connect(ssid, password)
    
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

async def main(watcher):
    await connect_wifi(watcher)
    
    print("Setting up RF IN")
    rf = RFDevice(rx_callback=watcher.button_pressed, glitch=1)
    rf.enable_rx()
            
    print("Now running, on port 80")
    
    server_task=asyncio.create_task(web.app.start_server(port=80))

    if not AP_MODE:
        mqtt_client=MQTTClient("TestPico","10.27.81.207",user="hamqtt", password="Sh@nima821")
        mqtt_client.connect()
        mqtt_client.publish("RF2MQTT/availability","online",retain=True)
        mqtt_client.disconnect()
    
    led=watcher.get_led(2)
    led.off()
    watcher.status_green.blink(on_time=1/4, off_time=1/4,n=4)

    # Not sure why I have to do things this way, but it works...
    while True:
        await asyncio.sleep(1) # Do nothing. Just wait for buttons to be pressed.
    
if __name__ == "__main__":
    watcher=Orchestrator()
    if watcher.config_button.value():
        # Reset
        print("Performing factory reset")
        os.unlink(SETTINGS_FILE)
        watcher.status_red.blink(on_time=1/4, off_time=1/4,n=4)
        
    led=watcher.get_led(2)
    led.blink(n=None)
    
    asyncio.run(main(watcher))