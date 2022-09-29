from cn105 import CN105
import time
ecodan = CN105("/dev/ecodan", 2400)

ecodan.connect()

result = ecodan.get_flow_return_dhw()
print(result)

result = ecodan.get_compressor_frequency()
print(result)

result = ecodan.get_zone_and_outside()
print(result)

result = ecodan.get_modes()
print(result)
