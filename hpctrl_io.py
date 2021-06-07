import Adafruit_MCP4725
import gpiozero
import time
import redis

r = redis.Redis()

r1 = gpiozero.LED(24)
r2 = gpiozero.LED(22)
r3 = gpiozero.LED(23)
r4 = gpiozero.LED(27)
r5 = gpiozero.LED(18)
r6 = gpiozero.LED(17)

dac = Adafruit_MCP4725.MCP4725(address=0x60)

while True:

    # r1 ------------------------------------
    x = r.get("hpctrl:r1")
    if x:
        x = int(x.decode())
        if x==1:
            r1.on()
        else:
            r1.off()
    else:
        r1.off()

    # ac1 -----------------------------------      
    x = r.get("hpctrl:ac1")
    if x:
        x = int(x.decode())
        if x==1:
            r4.on()
        else:
            r4.off()
    else:
        r4.off()

    # dac -----------------------------------      
    x = r.get("hpctrl:dac")
    if x:
        x = round(float(x.decode()))
        dac.set_voltage(x)
    else:
        dac.set_voltage(0)

    time.sleep(1)
