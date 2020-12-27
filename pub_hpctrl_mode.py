import time
import paho.mqtt.client as mqtt
import json
import sys
import redis

r = redis.Redis()

# ------------------------------------------------------
# MQTT 
# ------------------------------------------------------
mqtt_user = "emonpi"
mqtt_passwd = "emonpimqtt2016"
mqtt_host = "192.168.1.64"
mqtt_port = 1883
mqtt_topic = "emon/#"

def on_message(client, userdata, msg):
    pass

def on_connect(client, userdata, flags, rc):
    pass

mqttc = mqtt.Client()
mqttc.on_message = on_message
mqttc.on_connect = on_connect

try:
    mqttc.username_pw_set(mqtt_user, mqtt_passwd)
    mqttc.connect(mqtt_host, mqtt_port, 60)
    mqttc.loop_start()
except Exception:
    print ("Could not connect to MQTT")
else:
    print ("Connected to MQTT")

# -----------------------------------------------------

while True:

    if int(time.time())%10==0:
        mode = r.get("hpctrl:mode")
        if mode: 
            mode = int(mode.decode())
            mode_sh = 0
            mode_dhw = 0
            if mode==1: mode_sh = 1
            if mode==2: mode_dhw = 1

            mqttc.publish("emon/hpmon5/mode",mode)
            mqttc.publish("emon/hpmon5/mode_sh_elec",mode_sh)
            mqttc.publish("emon/hpmon5/mode_dhw_elec",mode_dhw)
            mqttc.publish("emon/hpmon5/mode_sh_heat",mode_sh)
            mqttc.publish("emon/hpmon5/mode_dhw_heat",mode_dhw)


       
        time.sleep(2.0)
    time.sleep(0.1)
    mqttc.loop(0)

# Close
mqttc.loop_stop()
mqttc.disconnect()


