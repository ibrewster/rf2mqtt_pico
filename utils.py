from mqtt import MQTTClient
from shelve import ShelveFile
from config import SETTINGS_FILE

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
