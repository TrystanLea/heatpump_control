import Adafruit_MCP4725
import gpiozero
import time
import redis

r = redis.Redis()

r1 = gpiozero.LED(9)
r2 = gpiozero.LED(5)
r3 = gpiozero.LED(26)
r4 = gpiozero.LED(19)

ac1 = gpiozero.LED(24)
ac2 = gpiozero.LED(12)

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
            ac1.on()
        else:
            ac1.off()
    else:
        ac1.off()

    # dac -----------------------------------      
    x = r.get("hpctrl:dac")
    if x:
        x = round(float(x.decode()))
        dac.set_voltage(x)
    else:
        dac.set_voltage(0)

    time.sleep(1)
