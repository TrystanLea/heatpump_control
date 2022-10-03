import time
import json
import sys
import redis
import datetime
import math
import logging
from cn105 import CN105

logging.basicConfig(filename='/home/pi/hpctrl.log', level=logging.DEBUG, format='%(asctime)s %(message)s')

ecodan = CN105("/dev/ecodan", 2400)
ecodan.connect()

# -----------------------------------------------------
# Test configuration
# -----------------------------------------------------
config = {
    "heating": [
        {"h":0,"set_point":5.0,"flowT":20.0,"mode":"min"}
    ]
}

def log(message):
    #print(message)
    logging.debug(message)
    
# -----------------------------------------------------
# Init
# -----------------------------------------------------    
log("--- hpctrl starting ---")

r = redis.Redis()

# -----------------------------------------------------
# Loop
# -----------------------------------------------------
d = datetime.datetime.now()
hour = d.hour

mode = "heating"
heating = False
state = 0
last_flowT_target = 0
time_since_heating_start = 0
turn_off_timer = 0

first_run = True

while 1: 

    if math.floor(time.time()%10)==0:
        
        # Load heat pump state from Ecodan via CN105
        
        hp = {"time":int(time.time()),"node":"ecodan"}
        
        result = ecodan.get_flow_return_dhw()
        for key in result: hp[key] = result[key]
        
        result = ecodan.get_compressor_frequency()
        for key in result: hp[key] = result[key]

        result = ecodan.get_zone_and_outside()
        for key in result: hp[key] = result[key]

        result = ecodan.get_modes()
        for key in result: hp[key] = result[key]
        
        # print(hp)
        
        r.rpush("emonhub:sub",json.dumps(hp))
        
        # x = r.get('hpctrl:config')
        # if x: 
        #     config = json.loads(x)
        #     log("config updated")
        #     r.delete('hpctrl:config')
        
        f = open('/opt/emoncms/modules/hpctrl/schedule.json')
        config = json.load(f)

        x = r.hget('input:lastvalue:30','value')
        if x: hp['roomT'] = float(x.decode())*10.0
        else: hp['roomT'] = 20.0                     # default heating on if no room temp sensor
        
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
    
        log("room:%.1f flow:%.3f return:%.3f outside:%.2f power:%d freq:%d" % (hp['roomT'],hp['flowT'],hp['returnT'],hp['outside'],hp['power'],hp['freq']))
        
        if first_run:
            first_run = False
            if hp['power']==1:
                state = 1
                log("Heatpump is ON, setting state = 1")
            else:
                log("Heatpump is OFF, setting state = 0")
            log("Heating set point: "+str(heating['set_point']))
        
        # -----------------------------------------------------
        # HEATING MODE
        # -----------------------------------------------------
        if mode=="heating":
            # ----------------------------------------------------------------
            # Thermostat
            # ----------------------------------------------------------------
            if float(hp['roomT'])>=(float(heating['set_point'])+0.195) and state!=0:
                # turn heat off for 60 seconds then turn heat pump off completely
                state = 0
                last_flowT_target = 0
                ecodan.set_temp(20.0)
                log("Turning heating off start");
                turn_off_timer = time.time()

            if hp['roomT']<=(heating['set_point']-0.195) and state!=1:
                log("Turning heating on");
                state = 1
                ecodan.set_power(1)
                ecodan.set_temp(20.0)
                time_since_heating_start = time.time()

            # Delayed turn off
            if turn_off_timer:
                if (time.time()-turn_off_timer)>=60:
                    log("Turning heating off complete");
                    ecodan.set_power(0)
                    turn_off_timer = 0
                    
            # ----------------------------------------------------------------
            # Heating flow temperature control
            # ----------------------------------------------------------------         
            if state==1:
                
                if heating['mode']=="min":
                    if (time.time()-time_since_heating_start)>=60:
                        rT1 = 24.0
                        dt1 = 2.8
                        rT2 = 28.5
                        dt2 = 2.5

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

                        flowT_target = math.ceil(flowT_target)

                        
                        if flowT_target>heating['flowT']: flowT_target = heating['flowT']
                        log("SH flow target: %.1f" % flowT_target)
                        ecodan.set_temp(flowT_target)
                else:
                    flowT_target = heating['flowT']
                    log("SH flow target: %.1f" % flowT_target)
                    ecodan.set_temp(flowT_target)
                    
        time.sleep(1.2)
    time.sleep(0.1)

# Close
sys.exit()