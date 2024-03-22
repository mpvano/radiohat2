"""
Embedded Python Blocks:

Each time this file is saved, GRC will instantiate the first class it finds
to get ports and parameters of your block. The arguments to __init__  will
be the parameters. All of them are required to have default values!
"""

import numpy as np
from gnuradio import gr
import pmt

from ctypes import *

class blk(gr.basic_block):  # other base classes are basic_block, decim_block, interp_block
    """Embedded Python Block example - a simple multiply const"""

    def __init__(self):
        gr.basic_block.__init__(
            self,
            name='libradiohat',   # will show up in GRC
            in_sig = None,
            out_sig = None
        )
        self.libradiohat = CDLL("/usr/lib/libradiohat.so")
        self.libradiohat.initVFO(0,7074000,12288000)
#        self.libradiohat.cachePLLDivisor(False);
        self.libradiohat.setVFO(7074000)
        self.libradiohat.initCodec()
        self.libradiohat.setADCVol(c_float(0.7))
        self.libradiohat.initControl()
        self.libradiohat.initVSWR()
        self.libradiohat.readForwardOnly.restype = c_float
        self.libradiohat.readVSWROnly.restype = c_float
        self.message_port_register_in(pmt.intern('readForward'))
        self.set_msg_handler(pmt.intern('readForward'),self.handle_freq)
        self.message_port_register_in(pmt.intern('readVSWR'))
        self.set_msg_handler(pmt.intern('readVSWR'),self.handle_freq)
        self.message_port_register_in(pmt.intern('freq'))
        self.set_msg_handler(pmt.intern('freq'),self.handle_freq)
        self.message_port_register_in(pmt.intern('ptt'))
        self.set_msg_handler(pmt.intern('ptt'),self.handle_ptt)
        self.message_port_register_in(pmt.intern('adc'))
        self.set_msg_handler(pmt.intern('adc'),self.handle_adc)
        self.message_port_register_in(pmt.intern('cwmode'))
        self.set_msg_handler(pmt.intern('cwmode'),self.handle_cwmode)
        self.cwmode = 0
        self.ptt = 9999
        self.VFO = 0
        return

    def readForward(self):
        return self.libradiohat.readForwardOnly(None)
    
    def readVSWR(self):
        return self.libradiohat.readVSWROnly(None)

    def isKeyDown(self):
        return self.libradiohat.isKeyInputActive(None)

    def handle_freq(self,msg):
        self.vfomsg = int(pmt.to_double(msg))
        if (self.VFO != self.vfomsg):
            self.libradiohat.setVFO(self.vfomsg)
            self.libradiohat.checkLPF(self.vfomsg,c_bool(0))
            self.VFO = self.vfomsg
        return

    def handle_ptt(self,msg):
        self.pttmsg = pmt.to_long(msg)
        if (self.pttmsg != self.ptt):
            if (self.cwmode and self.pttmsg):
                self.libradiohat.enableTX(c_bool(0),c_int(2))
            else:
                self.libradiohat.enableTX(c_bool(self.pttmsg),c_int(0))
            self.ptt = self.pttmsg
        if (self.ptt == 1):
            self.libradiohat.checkKeydown()
        return

    def handle_adc(self,msg):
        self.adcmsg = pmt.to_float(msg)
        self.libradiohat.setADCVol(c_float(self.adcmsg))
        return

    def handle_cwmode(self,msg):
        self.cwmode = pmt.to_long(msg)
        return

#

#    def work(self, input_items, output_items):
#        return 0



