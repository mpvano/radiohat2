# Please do not change this hardware control module for Quisk.
# It provides control of RadioHat hardware via dynamic library.

from __future__ import print_function
from __future__ import absolute_import
from __future__ import division

import sys, struct, time, traceback, math
from quisk_hardware_model import Hardware as BaseHardware
import _quisk as QS

from ctypes import *

ADCGAIN = 0.3
SHOW_METERS = True
DEBUG = 0

#WWV10ERROR = -140       # from Quisk S Meter "Frequency 10"
WWV10ERROR = 0       # from Quisk S Meter "Frequency 10"
SI5351Correction = int(WWV10ERROR * -100)

CORRECT_TX_CODEC = False
CORRECT_RX_CODEC = False
PLOT_ERROR = False
DEBUG_PID = False

CODEC_CLOCK = 12288000                      # Nominal 12.288Mhz as per data sheet
TX_CLOCK_DEFAULT = CODEC_CLOCK              # locks up faster if these are known
RX_CLOCK_DEFAULT = CODEC_CLOCK
TX_DEV_STRING = "I/Q Tx Sample Output"      # which "use" string defines each buffer
RX_DEV_STRING = "Radio Sound Output"
TX_SCALE =  -1.0/200000.0                   # adjust correction count for buffer size
RX_SCALE =  1.0/1000000.0


########## Simple Generic PID
class pid:
    def __init__(self,Kp=0,Ki=0,Kd=0,maxOut=1,minOut=-1,integralSum=0,prevErr=0,dt=1,pDEBUG=False):
        self.DEBUG = pDEBUG
        self.Kp = Kp
        self.Ki = Ki
        self.Kd = Kd
        self.maxOut = maxOut
        self.minOut = minOut
        self.integralSum = integralSum
        self.prevErr = prevErr
        self.dt = dt

    def pid(self, currentErr):
        self.integralSum += (currentErr * self.dt)
        output  = self.Kp * currentErr
        output += self.Ki * self.integralSum
        output += self.Kd * ((currentErr - self.prevErr) / self.dt)
        if self.DEBUG:
            print(self.integralSum, currentErr, self.prevErr, output)
        self.prevErr = currentErr
        return max(self.minOut, min(self.maxOut, output))

################# Object to maintain an auxiliary clock frequency for use as Codec clock
class CodecClock:
    def __init__(self, deviceString="",baseRate=CODEC_CLOCK,scale=0.000001,maxCorrect=1000,DEBUG=False,PLOT=False):
        self.deviceString = deviceString
        self.baseRate = baseRate
        self.scale = scale
        self.maxCorrect = maxCorrect
        self.currentClock = baseRate
#        self.thePid = pid(0.04, 0.0013, 0.58, maxOut=maxCorrect, minOut=-maxCorrect,dt=1)
        self.thePid = pid(0.015, 0.0013, 0.19, maxOut=maxCorrect, minOut=-maxCorrect,dt=1)
        self.correction = 1.0
        self.DEBUG = DEBUG
    
    # for now, the "rate" field in the status object has been repurposed as cr_correction
    def getCorrectedClock(self, newClock):
        for use, name, rate, latency, errors, level, dev_errmsg in QS.sound_errors():
            if use == self.deviceString:
                self.correction = (self.thePid.pid((latency-4500)/-30) * self.scale) + 1.0
                if PLOT_ERROR:
                    print(int(latency-4500)/-30)
                elif DEBUG_PID:
                    print(use, int((latency-4500)/-30), self.correction, self.currentClock)
        self.currentClock = newClock * self.correction
        return int(self.currentClock)
        
    def idle(self,newClock): # keep the inactive object awake? Probably not...
        #dummy = self.getCorrectedClock(newClock)
        return


#############################
class Hardware(BaseHardware):
    def __init__(self, app, conf):
        BaseHardware.__init__(self, app, conf)
        self.vfo = None
        self.mode = None
        self.band = None
        self.bandwidth = 15000  
        self.startupFrequency = 7074000
        self.repeater_freq = None  # original repeater output frequency
        try:
            self.repeater_delay = conf.repeater_delay
        except:
            self.repeater_delay = 0.25  # repeater frequency change delay in seconds
        self.repeater_time0 = 0         # time of repeater change in frequency

    def open(self):  # Called once to open the Hardware
        self.tick = 0
        self.transmitting = False
        self.wasTransmitting = False

        self.libradiohat = CDLL("/usr/lib/libradiohat.so")
        if self.libradiohat == 0:
            t = "Can't find LibRadiohat!!"
        else:
            self.TxCodecClock = CodecClock(deviceString=TX_DEV_STRING,baseRate=TX_CLOCK_DEFAULT,scale=TX_SCALE)
            self.RxCodecClock = CodecClock(deviceString=RX_DEV_STRING,baseRate=RX_CLOCK_DEFAULT,scale=RX_SCALE)
            self.AuxClock = CODEC_CLOCK

            self.libradiohat.initVFO(c_int(SI5351Correction),self.startupFrequency,self.AuxClock)
            self.libradiohat.initCodec()
            self.libradiohat.initControl()
            self.libradiohat.setADCVol(c_float(ADCGAIN))
            self.getADCVol = self.libradiohat.getADCVol
            self.getADCVol.restype = c_float
            self.vswrexists = self.libradiohat.initVSWR()
            
            if (self.vswrexists):
                self.readForwardOnly = self.libradiohat.readForwardOnly
                self.readVSWROnly = self.libradiohat.readVSWROnly
                self.readADCRaw = self.libradiohat.readADCRaw
                self.readForwardOnly.restype = c_float
                self.readVSWROnly.restype = c_float
                self.readADCRaw.restype = c_float
                self.power = 0
                self.lastPower = -1
                self.vswr = 0
                self.lastVswr = -1
                self.battery = 0 
                self.lastBattery= -1
                
            t = " *RadioHat*"
        return t


    def close(self):  # Called once to close the Hardware
        pass

        
    def ChangeFrequency(self, tune, vfo, source='', band='', event=None):
        theVfo = vfo
#        if tune > vfo:
#            if (vfo - tune) > self.bandwidth:
#                theVfo = tune + self.bandwidth
#        else:
#            if (tune - vfo) > self.bandwidth:
#                theVFO = tune - self.bandwidth
        self.libradiohat.setVFO(theVfo - self.transverter_offset)
        self.libradiohat.checkLPF(theVfo - self.transverter_offset, c_bool(0))
        if DEBUG:
            print(tune,vfo,theVfo)
        self.vfo = vfo
        return tune, theVfo


    def ReturnFrequency(self):
        # Return the current tuning and VFO frequency.  If neither have changed,
        # you can return (None, None).  This is called at about 10 Hz by the main.
        # return (tune, vfo) # return changed frequencies
        return None, None    # frequencies have not changed


    # Change frequency for repeater offset during Tx
    def RepeaterOffset(self, offset=None):
        if DEBUG:
            print("in repeater offset")
            print (offset)
        if offset is None:  # Return True if frequency change is complete
            if time.time() > self.repeater_time0 + self.repeater_delay:
                return True
        elif offset == 0:  # Change back to the original frequency
            if self.repeater_freq is not None:
                self.repeater_time0 = time.time()
                self.ChangeFrequency(self.repeater_freq, self.repeater_freq, "repeater")
                self.repeater_freq = None
        else:  # Shift to repeater input frequency
            self.repeater_time0 = time.time()
            self.repeater_freq = self.vfo
            if DEBUG:
                print(self.vfo, offset, int(offset * 1000))
            vfo = self.vfo + int(offset * 1000)  # Convert kHz to Hz
            self.ChangeFrequency(vfo, vfo, 'repeater')
        return False


    def GetStartupFreq(self):  # return the startup frequency
        return self.startupFrequency


    def GetFreq(self):  # return the running frequency
        return none,none


    def ChangeBand(self, band):
        # band is a string: "60", "40", "WWV", etc.
        BaseHardware.ChangeBand(self, band)
        self.band = band
        self.SetTxLevel()


    def ChangeMode(self, mode):
        # mode is a string: "USB", "AM", etc.
        BaseHardware.ChangeMode(self, mode)
        self.mode = mode
        QS.set_cwkey(0)
        self.SetTxLevel()


    def SetTxLevel(self):
        tx_level = self.conf.tx_level.get(self.band, 70)
        if self.mode[0:3] in ( "DGT", "FDV",):  # Digital modes; percentage of power
            reduc = self.application.digital_tx_level
        else:
            reduc = self.application.tx_level
        tx_level = int(tx_level * reduc / 100.0 + 0.5)
        if tx_level < 0:
            tx_level = 0
        elif tx_level > 100:
            tx_level = 100
        QS.set_mic_out_volume(tx_level)
        if DEBUG:
            print(self.getADCVol())
            print("Change tx_level to", tx_level)


    def OnSpot(self, level):
        pass


    def CorrectCodecSpeed(self):
        if (CORRECT_RX_CODEC or CORRECT_TX_CODEC):
            if (CORRECT_TX_CODEC and CORRECT_RX_CODEC):     # CORRECTING EACH SEPARATELY
                if self.transmitting:
                    self.RxCodecClock.idle(self.AuxClock)
                    self.AuxClock = self.TxCodecClock.getCorrectedClock(self.AuxClock)
                else:
                    self.TxCodecClock.idle(self.AuxClock)
                    self.AuxClock = self.RxCodecClock.getCorrectedClock(self.AuxClock)

            elif CORRECT_TX_CODEC:                          # ONLY CORRECTING TX 
                self.AuxClock = self.TxCodecClock.getCorrectedClock(self.AuxClock)

            elif CORRECT_RX_CODEC:                          # ONLY CORRECTING RX
                self.AuxClock = self.RxCodecClock.getCorrectedClock(self.AuxClock)

            self.libradiohat.setAuxClock(self.AuxClock)
        return


    # Called by Quisk when changing between Rx and Tx. "is_tx" is 0 or 1
    def OnChangeRxTx(self, is_tx):
        self.transmitting = is_tx
        self.libradiohat.enableTX(is_tx, 1)
        self.CorrectCodecSpeed()
        pass


    def PollCwKey(self):  # Called frequently by Quisk to check the CW key status
        if self.mode not in ('CWU', 'CWL'):
            return
        if (self.libradiohat.isKeyInputActive() != 0):
            QS.set_cwkey(1)
        else:
            QS.set_cwkey(0)
        pass


    def HeartBeat(self):  # Called at about 10 Hz by the main
        self.tick += 1
        if (self.tick % 10) == 0:
            self.CorrectCodecSpeed()
            
        if SHOW_METERS:
            phase = self.tick % 2
            if self.vswrexists and self.application.bottom_widgets:
                if (self.tick % 100) == 0:
                    self.battery = self.readADCRaw(1,0) * 10
                    if self.lastBattery != self.battery:
                        self.lastBattery = self.battery
                        self.application.bottom_widgets.UpdateVoltageText(self.battery)
                elif self.transmitting:
                    self.wasTransmitting = True
                    if phase == 1:
                        self.power = self.readForwardOnly()
                        if self.power != self.lastPower:
                            self.lastPower = self.power
                            self.application.bottom_widgets.UpdateFwdText(self.power)
                    elif phase == 0:
                        self.vswr = self.readVSWROnly()
                        if self.lastVswr != self.vswr:
                            self.lastVswr = self.vswr
                            self.application.bottom_widgets.UpdateVswrText(self.vswr)
                elif self.wasTransmitting:
                    self.wasTransmitting = False
                    self.application.bottom_widgets.UpdateFwdText(0)
                    self.application.bottom_widgets.UpdateVswrText(0)
        pass
