import time

from machine import Pin, Timer

from led import LED
from config import SETTINGS_FILE
from shelve import ShelveFile
from mqtt import MQTTClient

class Orchestrator:
    # Pin numbers
    LED_A_PIN=2
    LED_B_PIN=3
    LED_C_PIN=4
    LED_D_PIN=5
    
    STATUS_RED=6
    STATUS_GREEN=7
    POWER=8
    
    # GPIO "Pin" instances
    _LEDS={
        LED_A_PIN: LED(LED_A_PIN),
        LED_B_PIN: LED(LED_B_PIN),
        LED_C_PIN: LED(LED_C_PIN),
        LED_D_PIN: LED(LED_D_PIN),
        STATUS_GREEN:LED(STATUS_GREEN),
        STATUS_RED:LED(STATUS_RED),
        POWER:LED(POWER)
    }
    
    status_green=_LEDS[STATUS_GREEN]
    status_red=_LEDS[STATUS_RED]
    
    
    # button # to pin number lookup. No "button zero", so 0 is None
    BUTTON_PINS=[POWER, LED_A_PIN, LED_B_PIN, LED_C_PIN, LED_D_PIN, STATUS_GREEN, STATUS_RED]
    
    def __init__(self):
        self._BLINK_TIMERS={} # Initialize to an empty dict
        self._last_press=None # tuple of Remote ID, button, time
        self._learn_mode=False # For learning a new remote code/button. Must use the same protocol we know already.
        
        with ShelveFile(SETTINGS_FILE) as remote_file:
            self._known_remotes=remote_file.get('remotes',[])
            self._associations = remote_file.get('associations', {})
        
        self.config_button=Pin(14,Pin.IN,Pin.PULL_DOWN)
        self.config_button.irq(handler=self._config_released, trigger=Pin.IRQ_FALLING)
        self._config_timer=Timer()

            
    def get_led(self,pin):
        return self._LEDS[pin]
            
    def button_pressed(self,code,timestamp,bitlength,pulselength,proto):        
        # Decode the remote ID and button number from the code
        remote_id = code >> 4

        button = code & (0b1111)
        button_mask = 1
        button_num = 1
        while not button & button_mask:
            button_mask = button_mask << 1
            button_num += 1

        
        # Make sure this isn't a repeat of a button we have seen recently
        # If button is held down, we only want to respond once.
        try:
            last_remote, last_button, last_timestamp=self._last_press
        except (TypeError, ValueError):
            pass
        else:
            period=timestamp-last_timestamp # In microseconds
            if period<500000 and remote_id==last_remote and button_num==last_button:
                return # Don't process this button press, as we have seen it recently
        finally:
            self._last_press=(remote_id,button_num,timestamp)
            
        print("Processing signal from remote",remote_id,"Button",button_num)
        if self._learn_mode:
            if remote_id not in self._known_remotes:
                self._known_remotes.append(remote_id)
                with ShelveFile(SETTINGS_FILE) as remote_file:
                    remote_file['remotes']=self._known_remotes
                    
                print("Added remote with id", remote_id)
                self.status_green.blink(on_time=.3, off_time=.3, n=3)
            return
        
        if remote_id not in self._known_remotes:
            print("Ignoring message from remote", remote_id, "as it is not in our known remotes database")
            return #Ignore input from unknown remotes
        
        pin=self.BUTTON_PINS[button_num]
        self._LEDS[pin].blink(on_time=.5,off_time=0,n=1)
        if button_num in self._associations:
            self._associations[button_num](button_num)
            
        mqtt_client=MQTTClient("TestPico","10.27.81.207",user="hamqtt", password="Sh@nima821")
        mqtt_client.connect()
        mqtt_client.publish("RF2MQTT/remote/"+str(button_num),"ON")
        mqtt_client.disconnect()
        self.status_green.blink(on_time=1/7, off_time=1/7, n=4)
        
    def _config_released(self,pin):
        self._config_timer.init(mode=Timer.ONE_SHOT, period=100,callback=self._set_learn_mode)
        
    def _set_learn_mode(self,timer):
        self._learn_mode=not self._learn_mode
        if self._learn_mode:
            print("Entered Learn Mode")
            self.status_green.blink(n=None)
        else:
            print("Left Learn Mode")
            self.status_green.off()
                    