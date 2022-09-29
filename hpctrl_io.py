import gpiozero
import time
import redis
import serial

r = redis.Redis()

r4 = gpiozero.LED(27)

ser = serial.Serial("/dev/ecodan", 2400, 8, 'E', 1, 0.5)

last_power = -1
last_temp = -1

def calc_checksum(frame):
  frame_sum = 0
  for i in range(0,len(frame)-1):
    frame_sum += frame[i]
  frame[len(frame)-1] = (0xfc - frame_sum) & 0xff
  return frame

def read_reply():
  bid = 0
  length = 0
  data = []
  start_time = time.time()
  
  while (time.time()-start_time)<1.0:
    while ser.in_waiting:
      # Read in byte
      val = ord(ser.read(1))
      
      if len(data)<=bid:
        data.append(val)
      else:
        data[bid] = val

      # reset bid to 0 if first not sync byte
      if data[0]!=0xfc:
        bid = 0
      # Find length
      if bid==4:
        length = val + 5
      # Parse frame if we reach checksum
      if length!=0 and bid==length:
        parse_frame(data,length)
        bid = 0
      else: 
        # Increment byte id
        bid += 1

    time.sleep(0.1)

def parse_frame(data,length):

  print("rx "+str(len(data)))
  #for i in range(0,length+1):
   # #print(str(i)+" "+hex(data[i])+" "+str(data[i]))
  
  #zprint(list(map(hex,data)))
  
  response = data[5:]
  cmd = response[0]
  # print(response)
 
  if cmd==0x04:
    print("Compressor Frequency:"+str(response[1]));
 
 
  if cmd==0x0c:
    val = (response[1]<<8)+response[2]
    print("Flow:"+str(val*0.01));

    val = (response[4]<<8)+response[5]
    print("Return:"+str(val*0.01))
    
    val = (response[7]<<8)+response[8]
    print("DHW:"+str(val*0.01))
  
  if cmd==0x0b:
    val = (response[1]<<8)+response[2]
    print("Zone1T:"+str(val*0.01));

    val = (response[3]<<8)+response[4]
    print("Zone?:"+str(val*0.01));

    val = (response[7]<<8)+response[8]
    print("Zone2:"+str(val*0.01));
  
    print("Outside:"+str((response[11]/2)-40))

  if cmd==0x26:
    print("Power:"+str(response[3]))
    print("Operation Mode:"+str(response[4]))
    print("Hot Water Mode:"+str(response[5]))      
    print("Operation Mode:"+str(response[6]))     
     
    val = (response[8]<<8)+response[9]
    print("Hot water Set Point:"+str(val*0.01));
    val = (response[10]<<8)+response[11]
    print("Heating Set Point:"+str(val*0.01));
    val = (response[12]<<8)+response[13]
    print("Unknown Set Point:"+str(val*0.01));

def cn105_power(power):
    global last_power
    if power!=last_power:
        last_power = power
        print("Sending power cmd "+str(power))
        msg = [0xfc,0x41,0x02,0x7a,16,0x32,0x01,0x00,power,0x02,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00]
        msg = calc_checksum(msg)
        ser.write(msg)
        read_reply()

def cn105_temp(temp):
    global last_temp
    
    temp = int(temp*10)*0.1
    
    if temp!=last_temp:
        last_temp = temp
        
        z1sp_a = int(temp*100)>>8
        z1sp_b = int(temp*100) - (z1sp_a<<8)
        
        print("Sending temp cmd "+str(temp))
        msg = [0xfc,0x41,0x02,0x7a,16,0x32,0x80,0x00,0x00,0x02,0x00,0x00,0x00,0x00,0x00,z1sp_a,z1sp_b,0x00,0x00,0x00,0x00,0x00]
        msg = calc_checksum(msg)
        ser.write(msg)
        read_reply()

lastupdate = 0
while True:

    # r1 ------------------------------------     HP ON OFF
    x = r.get("hpctrl:r1")
    if x:
        x = int(x.decode())
        if x==1:
            cn105_power(1)
        else:
            cn105_power(0)
    else:
        cn105_power(0)

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
        cn105_temp(float(x))
    else:
        cn105_temp(float(0))

    """
    if (time.time()-lastupdate)>10:
        lastupdate = time.time()

        msg = [0xfc,0x42,0x02,0x7a,0x01,0x26,0x00]
        msg = calc_checksum(msg)
        ser.write(msg)
        read_reply()
    """
    time.sleep(1)
