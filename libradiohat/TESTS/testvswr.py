from time import sleep
from ctypes import *

vswrdac = CDLL('libradiohat.so')
if (not vswrdac.initVSWR()):
    print("libradiohat.so NOT FOUND")
else:
    print()
    readForwardOnly = vswrdac.readForwardOnly
    readVSWROnly = vswrdac.readVSWROnly
    readADCRaw = vswrdac.readADCRaw

    readForwardOnly.restype = c_float
    readVSWROnly.restype = c_float
    readADCRaw.restype = c_float

    while True:
        power = readForwardOnly()
        sleep(0.01)
        vswr = readVSWROnly()
        sleep(0.01)
        Battery = 10 * readADCRaw(1,0)
        
        print('%2.2f Watts %2.2f:1 SWR    %2.2f Volts' % ( power, vswr, Battery), end = '\r')
        sleep(1)
