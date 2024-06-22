print("Execution start")
import os

import uasyncio as asyncio

import web
import utils

from rf import RFDevice
from orchestrator import Orchestrator
from config import SETTINGS_FILE

async def main():
    watcher=Orchestrator()
    print("Init Called")
    if watcher.config_button.value():
        # Reset
        print("Performing factory reset")
        os.unlink(SETTINGS_FILE)
        watcher.status_red.blink(on_time=1/4, off_time=1/4,n=4)
        
    watcher.power_led.blink(n=None)
    watcher.status_red.on()
    
    wlan = await utils.connect_wifi(watcher)
    
    print("Setting up RF IN")
    rf = RFDevice(rx_callback=watcher.button_pressed, glitch=1)
    rf.enable_rx()
            
    print("Now running, on port 80")
    
    # Create the web server task
    server_task=asyncio.create_task(web.app.start_server(port=80))

    if not utils.SETTINGS['APMODE']:
        utils.publish_mqtt("RF2MQTT/availability","online",True)

    watcher.power_led.on()
    watcher.status_red.off()
    
    watcher.status_green.blink(period=1/4,n=4)
    
    # Create the WiFi watchdog task
    watchdog_task=asyncio.create_task(utils.check_wifi(wlan,watcher))
    print("init complete")

    # Main loop to just frequently yeild control to the event loop so new co-routines can be proceessed
    while True:
        await asyncio.sleep(15)
    
if __name__ == "__main__":
    asyncio.run(main())