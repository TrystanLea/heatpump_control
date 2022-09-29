from cn105 import CN105
import time
ecodan = CN105("/dev/ecodan", 2400)
"""
result = ecodan.get_flow_return_dhw()
print(result)

result = ecodan.get_compressor_frequency()
print(result)

result = ecodan.get_zone_and_outside()
print(result)
"""

commands = [1,2,3,4,5,6,7,9,11,12,13,14,16,17,19,20,21,23,24,25,26,28,29,163]
for i in commands:
  result = ecodan.get_request_raw(i)
  time.sleep(0.2)
