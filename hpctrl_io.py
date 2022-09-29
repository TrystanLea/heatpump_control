import gpiozero
import time
import redis
import serial
from cn105 import CN105

r = redis.Redis()
r4 = gpiozero.LED(27)

ecodan = CN105("/dev/ecodan", 2400)
ecodan.connect()

lastupdate = 0
while True:

    # r1 ------------------------------------     HP ON OFF
    x = r.get("hpctrl:r1")
    if x:
        x = int(x.decode())
        if x==1:
            ecodan.set_power(1)
        else:
            ecodan.set_power(0)
    else:
        ecodan.set_power(0)

    # ac1 -----------------------------------      3 WAY VALVE 
    x = r.get("hpctrl:ac1")
    if x:
        x = int(x.decode())
        if x==1:
            r4.on()
        else:
            r4.off()
    else:
        r4.off()

    # dac -----------------------------------     FLOW TEMP  
    x = r.get("hpctrl:temp")
    if x:
        ecodan.set_temp(float(x))
    else:
        ecodan.set_temp(float(0))

    time.sleep(1)
