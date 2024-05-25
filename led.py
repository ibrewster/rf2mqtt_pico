from machine import Pin
import uasyncio as asyncio

import micropython

class LED:
    def __init__(self,pin):
        self._gpio=Pin(pin, Pin.OUT)
        self._blink_task=None
        
        self._blink_stopped=asyncio.Event()
        self._blink_stopped.set()
        self._stop_blink=False
        
        
    def blink(self,on_time=.5, off_time=.5,n=1):
        if self._blink_task is not None:
            self._blink_task.data=asyncio.core.CancelledError
            self._blink_task = None
            
        task=asyncio.create_task(self._blink(on_time,off_time,n))
        self._blink_task=task
    
    def on(self):
        if self._blink_task is not None:
            self._blink_task.data=asyncio.core.CancelledError
            self._blink_task = None
            
        self._gpio.on()
    
    def off(self):
        if self._blink_task is not None:
            self._blink_task.data=asyncio.core.CancelledError
            self._blink_task = None

        self._gpio.off()
        
    def is_blinking(self):
        return self._blink_task is not None
        
    async def _blink(self,on_time=.5, off_time=.5,n=1):
        try:
            if n is not None:
                for count in range(n):
                    await self._blink_once(on_time,off_time)
            else:
                while True:
                    await self._blink_once(on_time,off_time)
        finally:
            self._blink_task=None
            
    async def _blink_once(self, on_time, off_time):
        self._gpio.on()
        await asyncio.sleep(on_time)
        self._gpio.off()
        await asyncio.sleep(off_time)
            