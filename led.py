from machine import Pin, Timer
import uasyncio as asyncio

import micropython


class LED:
    def __init__(self,pin):
        self._gpio=Pin(pin, Pin.OUT)
        self._blink_task=None
        self._timer_id=None
        self._blink_count=None
        self._max_blink=0
        
    def _stop_blink(self):
        if self._blink_task is not None:
            self._blink_task.deinit()
            self._blink_task=None
            self._blink_count=None
            self._max_blink=0
        self._gpio.off() # always end off.
            
        #if self._blink_task is not None:
        #    self._blink_task.data=asyncio.core.CancelledError
        #    self._blink_task = None
        
    def blink(self,period=.5,n=1):
        self.on() # Always start on.
        
        on_time=int(period*1000) # convert to milliseconds
        if n is not None:
            self._blink_count=1 # count the inital "on" as 1
            self._max_blink=n*2 #toggle on, toggle off.
        
        self._blink_task=Timer()
        self._blink_task.init(mode=Timer.PERIODIC, period=on_time, callback=self._blink)
        
        #task=asyncio.create_task(self._blink(on_time,off_time,n))
        #self._blink_task=task
                
    def on(self):
        self._stop_blink()
        self._gpio.on()
    
    def off(self):
        self._stop_blink()
        self._gpio.off()
        
    def is_blinking(self):
        return self._blink_task is not None
    
    def _blink(self,timer):
        if self._blink_count is not None:
            self._blink_count+=1
            if self._blink_count>=self._max_blink:
                return self._stop_blink()
            
        self._gpio.toggle()
        
    #async def _blink(self,on_time=.5, off_time=.5,n=1):
    #    try:
    #        if n is not None:
    #            for count in range(n):
    #                await self._blink_once(on_time,off_time)
    #        else:
    #            while True:
    #                await self._blink_once(on_time,off_time)
    #    finally:
    #        self._blink_task=None
            
    #async def _blink_once(self, on_time, off_time):
    #    self._gpio.on()
    #    await asyncio.sleep(on_time)
    #    self._gpio.off()
    #    await asyncio.sleep(off_time)
            