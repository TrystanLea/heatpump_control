import time
import paho.mqtt.client as mqtt
import json
import sys
import redis
import datetime
import math
import logging

logging.basicConfig(filename='/var/log/emoncms/hpctrl.log', level=logging.DEBUG, format='%(asctime)s %(message)s')

mqtt_user = "emonpi"
mqtt_passwd = "emonpimqtt2016"
mqtt_host = "192.168.1.64"
mqtt_port = 1883
mqtt_connected = False

frost_protection_temperature = 6.0

# -----------------------------------------------------
# Test configuration
# -----------------------------------------------------
config = {
    "heating": [
        # {"h":0,"set_point":19.5,"flowT":34.0,"mode":"min"}
    ],
    "dhw": [
        # {"start":"1500","T":40.0}
    ]
}
# -----------------------------------------------------
# Read in input values
# -----------------------------------------------------
hp = {'roomT':False,'flowT':False,'returnT':False,'cyl_top':False,'cyl_bot':False,'flowrate':False,'ambient':False}

def log(message):
    # print(message)
    logging.debug(message)


def on_message(client, userdata, msg):
    global hp, config
    if msg.topic=="hpctrl/config":
        config = json.loads(msg.payload)
        log("Config received")
    if msg.topic=="emon/emonth3/temperature":
        hp['roomT'] = round(float(msg.payload),2)

# -----------------------------------------------------
# Subscribe to relevant topics
# -----------------------------------------------------        
def on_connect(client, userdata, flags, rc):
    global mqtt_connected
    mqtt_connected = True
    mqttc.subscribe("hpctrl/config")
    mqttc.subscribe("emon/emonth3/temperature")

# -----------------------------------------------------
# Misc
# -----------------------------------------------------
def mqtt_pub(topic,message,repeat,delay):
    for i in range(repeat):
        mqttc.publish(topic,message)
        mqttc.loop(0)
        time.sleep(delay)

def temp_to_dac(temp):
    return round(819.2*((temp-7.5)/12.5))
    
def inputs_ready():
    ready = True
    for i in hp:
        if hp[i] is False:
            ready = False
    if not ready:
        log("waiting for inputs...")
    return ready
    
# -----------------------------------------------------
# Init
# -----------------------------------------------------    
r = redis.Redis()
    
mqttc = mqtt.Client()
mqttc.on_message = on_message
mqttc.on_connect = on_connect

# Connect
try:
    mqttc.username_pw_set(mqtt_user, mqtt_passwd)
    mqttc.connect(mqtt_host, mqtt_port, 60)
    mqttc.loop_start()
except Exception:
    log("Could not connect to MQTT")
else:
    log("Connected to MQTT")

# -----------------------------------------------------
# Loop
# -----------------------------------------------------
d = datetime.datetime.now()
hour = d.hour

mode = "heating"
heating = False
dhw_set_point = 0
state = 0
last_flowT_target = 0
time_since_heating_start = 0
frost_protection_state = 0
frost_protection_timer = 0

first_run = True

dhw_complete = 0

while 1: 

    if mqtt_connected:
        if math.floor(time.time()%10)==0:
        
            x = r.get('hpmon5:cyl_bot')
            if x: hp['cyl_bot'] = float(x.decode())
                
            x = r.get('hpmon5:cyl_top')
            if x: hp['cyl_top'] = float(x.decode())

            x = r.get('hpmon5:FlowT')
            if x: hp['flowT'] = float(x.decode())
            
            x = r.get('hpmon5:ReturnT')
            if x: hp['returnT'] = float(x.decode())

            x = r.get('hpmon5:FlowRate')
            if x: hp['flowrate'] = float(x.decode())

            x = r.get('hpmon5:ambient')
            if x: hp['ambient'] = float(x.decode())
            
            last_hour = hour
            d = datetime.datetime.now()
            h = d.hour
            m = d.minute
            
            # 1640 format
            if h<10: h = "0"+str(h) 
            else: h = str(h)
            if m<10: m = "0"+str(m) 
            else: m = str(m)
            hm = h+m
            
            # Work out current heating setpoint
            for period in config['heating']:
                if period['h']<=d.hour:
                    heating = period
            
            # Work out if we are at the start of a dhw run
            for run in config['dhw']:
                if run['start']==hm and mode=="heating":
                    mode = "dhw"
                    dhw_set_point = run['T']
                    log("Starting DHW cycle")
            
            if inputs_ready():
                log("room:%.1f flow:%.3f return:%.3f flowrate:%.3f cylt:%.2f cylb:%.2f ambient:%.2f" % (hp['roomT'],hp['flowT'],hp['returnT'],hp['flowrate'],hp['cyl_top'],hp['cyl_bot'],hp['ambient']))
                
                if first_run:
                    first_run = False
                    if hp['flowrate']>0.0:
                        state = 1
                        log("Heatpump is ON, setting state = 1")
                    else:
                        log("Heatpump is OFF, setting state = 0")
                    log("Heating set point: "+str(heating['set_point']))
                
                # -----------------------------------------------------
                # HEATING MODE
                # -----------------------------------------------------
                if mode=="heating":
                    # Dont start heating for 10 minutes after finishing DHW
                    if time.time()-dhw_complete>600:
                        # ----------------------------------------------------------------
                        # Thermostat
                        # ----------------------------------------------------------------
                        if hp['roomT']>=(heating['set_point']+0.195) and state!=0:
                            # turn heat off for 60 seconds then turn heat pump off completely
                            state = 0
                            r.set("hpctrl:dac",temp_to_dac(20.0))
                            #if hp['ambient']>4.0:
                            log("Turning heating off");
                            time.sleep(60)
                            r.set("hpctrl:r1",0)
                            time.sleep(25)
                            #else: 
                            #log("Frost protection");
                            # reset last_flowT_target
                            last_flowT_target = 0
                            frost_protection_state = 0
                            frost_protection_timer = time.time()

                        if hp['roomT']<=(heating['set_point']-0.195) and state!=1:
                            log("Turning heating on");
                            state = 1
                            r.set("hpctrl:r1",1)
                            r.set("hpctrl:dac",temp_to_dac(20.0))
                            time_since_heating_start = time.time()
                            time.sleep(60)

                        # frost protection
                        if state==0:
                            if hp['ambient']>6.0:
                                if frost_protection_state==1:
                                    log("Frost protection pump off")
                                    frost_protection_state=0
                                    frost_protection_timer=0
                                    r.set("hpctrl:r1",0)
                            else:
                                if frost_protection_state==0:
                                    # if off for 20 minutes
                                    if (time.time()-frost_protection_timer)>1800:
                                        frost_protection_timer = time.time()
                                        frost_protection_state=1
                                        log("Frost protection pump on")
                                        r.set("hpctrl:r1",1)
                                        r.set("hpctrl:dac",temp_to_dac(20.0))
                                if frost_protection_state==1:
                                    # if on for 10 minutes
                                    if (time.time()-frost_protection_timer)>600:
                                        frost_protection_timer = time.time()
                                        frost_protection_state=0
                                        log("Frost protection pump off")
                                        r.set("hpctrl:r1",0)
                                        r.set("hpctrl:dac",temp_to_dac(18.0))
                        # ----------------------------------------------------------------
                        # Heating flow temperature control
                        # ----------------------------------------------------------------         
                        if state==1:
                            
                            if heating['mode']=="min":
                                rT1 = 24.0
                                dt1 = 3.2
                                rT2 = 28.5
                                dt2 = 3.3

                                m = (dt2-dt1)/(rT2-rT1)
                                c = dt1-(m*rT1)
                                dt = (m*hp['returnT'])+c
                            
                                flowT_target = hp['returnT']+dt
                                
                                # Do not allow flowT_target to decrease during heating cycle
                                # this is to avoid a defrost reducing the setpoint
                                if (time.time()-time_since_heating_start)<300:
                                    last_flowT_target = flowT_target
                                else:
                                    if flowT_target<last_flowT_target:
                                        flowT_target = last_flowT_target
                                    else:
                                        last_flowT_target = flowT_target

                                if (time.time()-time_since_heating_start)>900:
                                    flowT_target = math.ceil(flowT_target)

                                
                                if flowT_target>heating['flowT']: flowT_target = heating['flowT']
                            else:
                                flowT_target = heating['flowT']
                                
                            log("SH flow target: %.1f" % flowT_target)
                            r.set("hpctrl:dac",temp_to_dac(flowT_target))
                            r.set("hpctrl:mode",1)
                            mqttc.loop(0)
                        else:
                            r.set("hpctrl:mode",0)
                            mqttc.loop(0)
                        
                else:
                    # -----------------------------------------------------
                    # DHW MODE
                    # -----------------------------------------------------
                    r.set("hpctrl:mode",2)
                    mqttc.loop(0)
                    
                    if hp['cyl_top']<dhw_set_point or hp['cyl_bot']<(dhw_set_point-3.0):
                        flowT_target = hp['cyl_bot'] + 10.0
                        log("DHW flow target: %.1f" % flowT_target)
                        r.set("hpctrl:r1",1)
                        r.set("hpctrl:ac1",1)
                        r.set("hpctrl:dac",temp_to_dac(flowT_target))
                        mqttc.publish("emon/hpmon5/target",flowT_target)
                        mqttc.loop(0)
                        state = 1
                    else:
                        log("DHW heat up complete")
                        r.set("hpctrl:dac",temp_to_dac(20.0))                   # 1. Turn heat off
                        r.set("hpctrl:ac1",0)                                   # 2. Turn pump off
                        time.sleep(25)
                        r.set("hpctrl:r1",0)                                    # 3. Turn DHW relay off
                        time.sleep(25)
                        state = 0
                            
                        # Switch mode back to heating
                        mode = "heating"
                        # reset last_flowT_target
                        last_flowT_target = 0
                        # set dhw_complete timeout
                        dhw_complete = time.time()
                        
            time.sleep(2.0)
    time.sleep(0.1)

# Close
mqttc.loop_stop()
mqttc.disconnect()
sys.exit()

