import micropython
import machine

from microdot import Microdot,Response
from microdot.utemplate import Template

from config import SETTINGS_FILE
from shelve import ShelveFile

app = Microdot()

@app.route('/')
async def index(request):
    with ShelveFile(SETTINGS_FILE) as settings:
        mqtt_broker = settings.get('mqtt_broker', '')
        mqtt_user = settings.get('mqtt_user', '')
        mqtt_password = settings.get('mqtt_password', '')
        mqtt_channel = settings.get('mqtt_channel', '')
        
        wifi_ssid=settings.get('wifi_ssid','')
        wifi_password=settings.get('wifi_password','')
    
    template_args={
        'mqtt_broker': mqtt_broker,
        'mqtt_user': mqtt_user,
        'mqtt_password': mqtt_password,
        'mqtt_channel': mqtt_channel,
        'wifi_ssid': wifi_ssid,
        'wifi_password': wifi_password
    }
    
    template = Template('index.html').render(**template_args)    
    return Response(body=template,headers={'Content-Type':'text/html'})

@app.route('/setWiFi', methods=["POST"])
def setWiFi(request):
    ssid = request.form.get('wifi_ssid')
    password = request.form.get('wifi_password')
        
    with ShelveFile(SETTINGS_FILE) as settings:
        settings['wifi_ssid'] = ssid
        settings['wifi_password']=password

    micropython.schedule(lambda x: machine.reset(),0)
    return Response.redirect('/')

@app.route('/setMQTT', methods=["POST"])
def setMQTT(request):
    with ShelveFile(SETTINGS_FILE) as settings:
        for setting in request.form:
            settings[setting] = request.form[setting]
            
    return Response.redirect('/')