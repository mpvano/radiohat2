################################################### May 26, 2024 at 11:02:46 AM CDT
#
#   Microkeyer in python for raspberry pi
#
#   by Mario Vano, AE0GL
#
#   ...Keyer based on:
#       Iambic Morse Code Keyer Sketch (GPL2.1)
#       Copyright (c) 2009 Steven T. Elliott
#       http://openqrp.org/?p=343
#       ..."Trimmed" by Bill Bishop - wrb[at]wrbishop.com
#       ...rewritten for CircuitPython by Mario Vano AE0GL
#
#   Things to improve:
#
#   * Currently requires a hardware jumper between output and
#   transceiver input pin instead of a soft solution. This also
#   means it must be running, even to use a straight key.
#
#   * It's own monitor option would be nice
#
#   * Needs a UI thread to allow speed control, macros and keyboard input
#
#   * because libgpio cannot do pullup resistor configuration, this code requires
#     that it be done at boot time in /boot/firmware/config.txt by:
#         gpio=14,15,16,17=ip,pu
#
#import pwmio
import sys
import time
import gpiod


#   Startup Options
#gVOLUME = 1000     # 1-32767 pwm sidetone volume
gSPEED = 13 if (len(sys.argv) < 2) else int(sys.argv[1])
gIAMBICB = False    # otherwise it's iambic A
gLRSWAP = False      #  0 for normal, 1 for swap Dit and Dah inputs


##############################################################################
#   CREATE PIN OBJECTS

try:
    chip = gpiod.Chip('gpiochip4') # gpiochip4 for pi 5 otherwise gpiochip0
except FileNotFoundError:
    chip = gpiod.Chip('gpiochip0') # gpiochip4 for pi 5 otherwise gpiochip0

#   Key inputs
gSkPin = chip.get_line(17)     # straight key = PIN 11
gSkPin.request(consumer="KEYER", type=gpiod.LINE_REQ_DIR_IN)
#gSKPin.pull = Pull.UP
gLPin = chip.get_line(14)     # Left paddle in = PIN 8
gLPin.request(consumer="KEYER", type=gpiod.LINE_REQ_DIR_IN)
#gLPin.pull = Pull.UP
gRPin = chip.get_line(15)     # Right paddle in = PIN 10
gRPin.request(consumer="KEYER", type=gpiod.LINE_REQ_DIR_IN)
#gRPin.pull = Pull.UP

# NEG Going OUTPUT ON PIN 36 (not for wire OR!)
gTxPin = chip.get_line(16)
gTxPin.request(consumer="KEYER", type=gpiod.LINE_REQ_DIR_OUT)

#   Piezo sounder on pwm output for monitoring
#gTonePin = pwmio.PWMOut(board.SCK, duty_cycle=0, frequency=700)


# These make things a little more readable
def SkIsKeyed():
    return not gSkPin.get_value()

def DitIsKeyed():
    if gLRSWAP:
        return not gLPin.get_value()
    else:
        return not gRPin.get_value()

def DahIsKeyed():
    if gLRSWAP:
        return not gRPin.get_value()
    else:
        return not gLPin.get_value()

#   return process time in milliseconds - varies from board to board
#    return time.monotonic() * 1000         # how to do it on simpler CPUs
def millis():
    return time.monotonic_ns() / 1000000

#   everything needed to switch outputs between key up and key down
def keyerKey(keyed):
#    gTonePin.duty_cycle = gVOLUME if keyed else
    gTxPin.set_value(0 if keyed else 1)
    

# for a DAC pin returning returns 0-65535
#    if wpm is 0:
#        wpm = (gSpeedPin.value / 66) / 25
def getDitTimeFromWPM(wpm):
    return 1200 / (max(5, wpm))


###############################################################################
#                       IAMBIC KEYER (as main loop for now!)
try:
    #   State Machine constants
    kIDLE = 0
    kCHK_SK = 1
    kCHK_DIT = 2
    kCHK_DAH = 3
    kKEYED_PREP = 4
    kKEYED = 5
    kINTER_ELEMENT = 6

    #   keyerControl flag bit definitions
    kDIT_L = 0x01       #  Dit latch
    kDAH_L = 0x02       #  Dah latch
    kDIT_PROC = 0x04    #  An iambic Dit is being processed


    #   State Machine "Loop" (calls millis() for timing)
    keyerState = kIDLE
    lastState = kIDLE
    keyerControl = 0    # contains processing flags and keyer mode bits

    print(gSPEED,"WPM - type Ctrl-C to quit")
    while True:
        time.sleep(0.001)           # 1 ms loop delay

        # awaiting any cycle start from key, paddle, UI, (or cycle to continue via flag bit)
        if keyerState == kIDLE:
            ditTime = getDitTimeFromWPM(gSPEED)
            
            if SkIsKeyed():
                keyerKey(True)
                keyerState = kCHK_SK
            elif keyerControl & 0x03:  # honor an Iambic bit request?
                keyerState = kCHK_DIT
            elif DitIsKeyed():
                keyerControl |= kDIT_L
                keyerState = kCHK_DIT
            elif DahIsKeyed():
                keyerControl |= kDAH_L
                keyerState = kCHK_DIT
            else:
                keyerControl = 0
                keyerKey(False)

        # Waiting for Straight key release
        elif keyerState == kCHK_SK:
            if not SkIsKeyed():
                keyerKey(False)
                keyerState = kIDLE

        # confirm (once) whether was a dit or iambic equivalent
        elif keyerState == kCHK_DIT:
            if (keyerControl & kDIT_L) != 0:  # YES, treat as dit
                keyerControl |= kDIT_PROC
                ktimer = ditTime
                keyerState = kKEYED_PREP
            else:
                keyerState = kCHK_DAH  # otherwise see if it's a dah


        # adjust (once) delay for dit or dah (or iambic equivalent)
        elif keyerState == kCHK_DAH:
            if (keyerControl & kDAH_L) != 0:  # YES, treat as dah
                ktimer = ditTime * 3
                keyerState = kKEYED_PREP
            else:
                keyerState = kIDLE  # otherwise it was noise


        # activate (once) transmitter and sidetone and save correct element end time
        elif keyerState == kKEYED_PREP:
            keyerKey(True)
            ktimer += millis()                  # set timer for end of element
            keyerControl &= ~(kDIT_L | kDAH_L)  # clear paddle latch bits
            keyerState = kKEYED

        # Waiting for element timer to exceed current time
        elif keyerState == kKEYED:
            if millis() > ktimer:
                keyerKey(False)
                ktimer = millis() + ditTime     # set the inter-element silence time
                keyerState = kINTER_ELEMENT
            elif gIAMBICB:                      # Iambic B is different!
                if not gRPin.get_value():       # it keeps on if any paddles are down
                    keyerControl |= kDIT_L
                if not gLPin.get_value():
                    keyerControl |= kDAH_L

        # Waiting for interelement silence timer to expire
        elif keyerState == kINTER_ELEMENT:
            if DitIsKeyed():                    # ...but looking ahead for next element
                keyerControl |= kDIT_L
            if DahIsKeyed():
                keyerControl |= kDAH_L
            if millis() > ktimer:               # silence has expired
                if keyerControl & kDIT_PROC:    # if we thought it was a dit
                    keyerControl &= ~(kDIT_L | kDIT_PROC)  # clear dit flags
                    keyerState = kCHK_DAH       # or was it really a dah?
                else:
                    keyerControl &= ~kDAH_L     # it was a dah, clear latch
                    keyerState = kIDLE          # go idle

finally:
    gLPin.release()
    gRPin.release()
    gTxPin.release()
    gSkPin.release()
