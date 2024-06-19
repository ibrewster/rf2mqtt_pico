print("Execution start")
import network
import os
import time
import rp2

import uasyncio as asyncio
from machine import Timer, Pin, reset

import web
import utils

from rf import RFDevice
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
        utils.publish_mqtt("RF2MQTT/availability","online",True)

    watcher.power_led.on()
    watcher.status_green.blink(on_time=1/4, off_time=1/4,n=4)

    # Main loop just keeps tabs on the WiFi connection
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
        await asyncio.sleep(15) # Do nothing. Just wait for buttons to be pressed.
    
if __name__ == "__main__":
    watcher=Orchestrator()
    if watcher.config_button.value():
        # Reset
        print("Performing factory reset")
        os.unlink(SETTINGS_FILE)
        watcher.status_red.blink(on_time=1/4, off_time=1/4,n=4)
        
    watcher.power_led.blink(n=None)
    
    asyncio.run(main(watcher))