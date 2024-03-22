/*
***************************************** March 20, 2024 at 7:09:52 AM CDT
*****************************************************************************
*
*	Band and mode switching control logic
*	
*	started by Mario Vano AE0GL, February 2022
*
*	To generate the old method of relay controls via Pi GPIO:
*		#define USE_ALL_GPIO
*
*	In any case, the Pi GPIOs reserved for tx and rx mixer controls
*	and keydown testing are used to simplify use with other programs.
*
*	In either case, I2C control is attempted as well.
*
*	The Codec module is also used to change audio routing as needed.
*
******************************************************************************
*****************************************************************************/
#include <stdlib.h>
#include <stdio.h>
#include <unistd.h>
#include <stdint.h>
#include <fcntl.h>
#include <sys/ioctl.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <linux/i2c-dev.h>
#include <gpiod.h>

#include "control.h"
#include "codec.h"

void checkRelays(uint32_t frequency, bool nocache);	//	forward reference


/*
***************************************************************************
*
*	GPIO Assignments:
*
*		GPIOs I’m not using (I’ve used up the SPI pins for GPIO)
*			4
*		These are still free but try to avoid them for future use:
*			5,6		Pi built-in shutdown detection
*			4	is used by Pimoroni power switch shim
*		UART - 14: TXD, 15: RXD, 16: RTS, 17: CTS
*
*	These are using GPIO numbering, despite the use of WiringPi.
*
*	Wiring Pi is buggy and poorly maintained, so it probably needs
*	to be phased out. In particular, pull up/down controls
*	fail silently to take effect on Pi 4.
*
*	Note that the recommended way to initialize GPIO now seems to be
*	in config.txt or in the ID EEPROM, since these pins are hard wired
*	and dedicated to most peripheral hardware. Something like this should
*	do the trick (untested).
*
*		gpio=7-13=op,dl
*		gpio=22,23=op,dh
*		gpio=24-27=ip,pu
*		gpio=17=a3
*
****************************************************************************/
#define	CONSUMER	"RadioHat"
char const * chipname = "gpiochip0";
char const * chipname5 = "gpiochip4";		// for pi 5 ONLY
struct gpiod_chip *gChip;

//	LIBGPIOD helper for opening output lines
struct gpiod_line * openLineForOutput(int gpioNum)
{
struct gpiod_line * theLine;

	if (	(theLine = gpiod_chip_get_line(gChip, gpioNum))
		&&	((gpiod_line_request_output(theLine, CONSUMER, 0) >= 0))
		) return theLine;
	else
		{
		if (theLine) gpiod_line_release(theLine);
		return 0;
		}
}

//	LIBGPIOD helper for opening input lines
struct gpiod_line * openLineForInput(int gpioNum, bool withPullup)
{
struct gpiod_line * theLine;
int theFlags = withPullup	? GPIOD_LINE_REQUEST_FLAG_BIAS_PULL_UP
							: GPIOD_LINE_REQUEST_FLAG_BIAS_DISABLE;

	if (	(theLine = gpiod_chip_get_line(gChip, gpioNum))
		&&	((gpiod_line_request_input_flags(theLine, CONSUMER, theFlags) >= 0))
		) return theLine;
	else
		{
		if (theLine)
			gpiod_line_release(theLine);
		return 0;
		}
}

//	LIBGPIOD helpers for writing  and reading output lines
bool gpioWrite(struct gpiod_line * line, int val)
{
	return gpiod_line_set_value(line, val);
}

int gpioRead(struct gpiod_line * line)
{
	return gpiod_line_get_value(line);
}


#ifdef USE_ALL_GPIO
//	SEE BELOW: 0-6 are RESERVED
//	Unique to my transceiver box
#define GPIO_RSTFilter	26		//	pulsed to reset latching relays
#define GPIO_B1Filter	7		//	10 meters - NOTE: Relay DISABLES filter 
#define GPIO_B2Filter	8		//	15 meters
#define GPIO_B3Filter	9		//	20 meters
#define GPIO_B4Filter	10		//	40 meters
#define GPIO_B5Filter	11		//	80 meters
#define GPIO_TXRXRelay	12		//	High switches TX->Filters else RX->Filters
#define GPIO_PWRAMP_ON	13		//	High enables Power amp Bias
//	14-21 are RESERVED
#define GPIO_notTX		22		//	a low enables the tx mixer HW
#define GPIO_notRX		23		//	a low enables the rx mixer HW

//	For current and future features of this software
#define GPIO_KeyerDIT	24		//	hw keying and ptt inputs
#define GPIO_KeyerDAH	25
#define GPIO_PTTIn		26
#define GPIO_Keyer_KEYDOWN GPIO_KeyerDAH

//////////////////////////////////////////////////////////////////////////////
//	THE REST ARE RESERVED AND SHOULDN'T BE USED BY THIS MODULE
#define GPIO_ID_SD		0		//	I2C RESERVED BY OPERATING SYSTEM
#define GPIO_ID_SC		1		//	I2C RESERVED BY OPERATING SYSTEM
#define GPIO_SDA		2		//	RESERVED FOR GENERAL PURPOSE I2C
#define GPIO_SCL		3		//	RESERVED FOR GENERAL PURPOSE I2C
#define GPCLK0			4		//	RESERVED FOR ONEWIRE BUS
#define GPIO_SHUTDOWN1	5		//	pin 1 of gpio-shutdown overlay switch
#define GPIO_SHUTDOWN2	6		//	pin 2 of gpio-shutdown overlay switch

#define GPIO_UART0_TX	14		//	RESERVED
#define GPIO_UART0_RX	15		//	RESERVED
#define GPIO_CTS		16		//	RESERVED
#define GPIO_RTS		17		//	WSJT-X and others can assert RTS for PTT

#define GPIO_PCM_CLK	18		//	USED BY AUDIO HARDWARE I2S
#define GPIO_PCM_FS		19		//	USED BY AUDIO HARDWARE I2S
#define GPIO_PCM_DIN	20		//	USED BY AUDIO HARDWARE I2S
#define GPIO_PCM_DOUT	21		//	USED BY AUDIO HARDWARE I2S
//////////////////////////////////////////////////////////////////////////////

//	needs globals to store handles for now
struct gpiod_line * GPIO_RSTFilter_line; 
struct gpiod_line * GPIO_B1Filter_line; 
struct gpiod_line * GPIO_B2Filter_line; 
struct gpiod_line * GPIO_B3Filter_line; 
struct gpiod_line * GPIO_B4Filter_line; 
struct gpiod_line * GPIO_B5Filter_line; 
struct gpiod_line * GPIO_TXRXRelay_line; 
struct gpiod_line * GPIO_PWRAMP_ON_line;
struct gpiod_line * GPIO_notTX_line;
struct gpiod_line * GPIO_notRX_line;
struct gpiod_line * GPIO_KeyerDIT_line; 
struct gpiod_line * GPIO_KeyerDAH_line;
struct gpiod_line * GPIO_PTTIn_line;


//	opens all the lines and saves global handles to them
bool initGPIO()
{
bool result = false;
struct gpiod_chip * line;

	gChip = gpiod_chip_open_by_name(chipname5);		//	will fail unless rpi 5
	if (!gChip)
		gChip = gpiod_chip_open_by_name(chipname);
	if (!gChip)
		{
		//	setup the output lines
		result = (	(GPIO_RSTFilter_line 	= openLineForOutput(GPIO_RSTFilter))
				 &&	(GPIO_B2Filter_line 	= openLineForOutput(GPIO_B2Filter))
				 &&	(GPIO_B3Filter_line 	= openLineForOutput(GPIO_B3Filter))
				 &&	(GPIO_B4Filter_line 	= openLineForOutput(GPIO_B4Filter))
				 &&	(GPIO_B5Filter_line 	= openLineForOutput(GPIO_B5Filter))
				 &&	(GPIO_TXRXRelay_line 	= openLineForOutput(GPIO_TXRXRelay))
				 &&	(GPIO_PWRAMP_ON_line 	= openLineForOutput(GPIO_PWRAMP_ON))
				 &&	(GPIO_notTX_line 		= openLineForOutput(GPIO_notTX))
				 &&	(GPIO_notRX_line 		= openLineForOutput(GPIO_notRX))
				 &&	(GPIO_B1Filter_line 	= openLineForOutput(GPIO_B1Filter))
				 );	
		if (!result)
			perror("Requesting line(s) as output failed\n");
		else
		    {
		    //	setup the input lines
		    //	These pins are monitored by this program for keying
		    result = (	(GPIO_KeyerDIT_line = openLineForInput(GPIO_KeyerDIT, true))
				 	&&	(GPIO_KeyerDAH_line = openLineForInput(GPIO_KeyerDAH,true))
				 	&&	(GPIO_PTTIn_line 	= openLineForInput(GPIO_PTTIn,true))
					);
			if (!result)
				perror("Requesting line(s) as input failed\n");
			}				
		}
	
	if (result)
		{
		//	Init QRP Labs filter board connected via O.C. Level shifters
		//	at startup, LPF is set to 10 meters
		//	Two O.C. Level shifters on that board control Ant Switch and Power Amp
		//	These GPIO pins enable the Hat's TX and RX mixers
		//	rx is enabled and tx and power amp are disabled
		result = (	(gpiod_line_set_value(GPIO_TXRXRelay_line, 0) >= 0)
				&&	(gpiod_line_set_value(GPIO_PWRAMP_ON_line, 0) >= 0)
				&&	(gpiod_line_set_value(GPIO_notTX_line,1) >= 0)
				&	(gpiod_line_set_value(GPIO_notRX_line, 0) >= 0)
				);
		if (!result)
			perror("Setting output lines failed\n");
		}

	if (!result && gChip)
		gpiod_chip_close(gChip);

	return result;
}

/*
*****************************************************************************
*	support functions for QRP labs filter board
*
*	Note that the QRP labs filter board has funny wiring for filter 1.
*	It is DISABLED by activating the coil! (I think - it's confusing!)
****************************************************************************/

//	called to see if need to update LPF setting
//	The cache argument is only used with latching relays to decide whether
//	we can skip the tedious and slow switching procedure they require.
void checkLPF_GPIO(uint32_t frequency, bool nocache)
{
const uint32_t LPF1_LIMIT = 30000000L;
const uint32_t LPF2_LIMIT = 21500000L;
const uint32_t LPF3_LIMIT = 14500000L;
const uint32_t LPF4_LIMIT = 7500000L;
const uint32_t LPF5_LIMIT = 4000000L;

static int lastfilter = -1;
int thefilter;

	if (frequency < LPF5_LIMIT)			thefilter = 5;
	else if (frequency < LPF4_LIMIT)	thefilter = 4;
	else if (frequency < LPF3_LIMIT)	thefilter = 3;
	else if (frequency < LPF2_LIMIT)	thefilter = 2;
	else thefilter = 1;
	
	//	Should rewrite to use a constant table for clarity and efficiency
	if (nocache || (lastfilter != thefilter))
		{
		switch (thefilter)		//	enable the correct filter
			{
			default:
			case 1:
				gpioWrite(GPIO_B1Filter_line, 0);	//	filter one enabled
				gpioWrite(GPIO_B2Filter_line, 0);
				gpioWrite(GPIO_B3Filter_line, 0);
				gpioWrite(GPIO_B4Filter_line, 0);
				gpioWrite(GPIO_B5Filter_line, 0);
				break;
			case 2:
				gpioWrite(GPIO_B1Filter_line, 1);	//	filter one disabled
				gpioWrite(GPIO_B2Filter_line, 1);
				gpioWrite(GPIO_B3Filter_line, 0);
				gpioWrite(GPIO_B4Filter_line, 0);
				gpioWrite(GPIO_B5Filter_line, 0);
				break;
			case 3:
				gpioWrite(GPIO_B1Filter_line, 1);	//	filter one disabled
				gpioWrite(GPIO_B2Filter_line, 0);
				gpioWrite(GPIO_B3Filter_line, 1);
				gpioWrite(GPIO_B4Filter_line, 0);
				gpioWrite(GPIO_B5Filter_line, 0);
				break;
			case 4:
				gpioWrite(GPIO_B1Filter_line, 1);	//	filter one disabled
				gpioWrite(GPIO_B2Filter_line, 0);
				gpioWrite(GPIO_B3Filter_line, 0);
				gpioWrite(GPIO_B4Filter_line, 1);
				gpioWrite(GPIO_B5Filter_line, 0);
				break;
			case 5:
				gpioWrite(GPIO_B1Filter_line, 1);	//	filter one disabled
				gpioWrite(GPIO_B2Filter_line, 0);
				gpioWrite(GPIO_B3Filter_line, 0);
				gpioWrite(GPIO_B4Filter_line, 0);
				gpioWrite(GPIO_B5Filter_line, 1);
				break;
			}
		lastfilter = thefilter;		//	update the cache
		}
}
#else	// USE_ALL_GPIO

/*
*****************************************************************************
* This version of the control code uses minimal GPIO functionality.
*
* Note that the I2C functionality is always attempted - either way -
* but is not used if the I2C gpio devices are missing at run time.
*
*****************************************************************************/

#define GPIO_notTX		22		//	a low enables the tx mixer HW
#define GPIO_notRX		23		//	a low enables the rx mixer HW

//	For current and future features of this module
#define GPIO_KeyerDIT	24		//	hw keying and ptt inputs
#define GPIO_KeyerDAH	25
#define GPIO_PTTIn		26


//	needs globals to store handles for now
struct gpiod_line * GPIO_notTX_line;
struct gpiod_line * GPIO_notRX_line;
struct gpiod_line * GPIO_KeyerDIT_line; 
struct gpiod_line * GPIO_KeyerDAH_line;
struct gpiod_line * GPIO_PTTIn_line;



//	opens all the lines and saves global handles to them
bool initGPIO()
{
bool result = false;
struct gpiod_chip * line;

	gChip = gpiod_chip_open_by_name(chipname5);
	if (!gChip)
		gChip = gpiod_chip_open_by_name(chipname);
	if (!gChip)
		perror("Open chip failed\n");
	else
		{
		//	setup the output lines
		result = ((GPIO_notTX_line 		= openLineForOutput(GPIO_notTX))
				 &&	(GPIO_notRX_line 	= openLineForOutput(GPIO_notRX))
				 );	
		if (!result)
			perror("Requesting line(s) as output failed\n");
		else
		    {
		    //	setup the input lines
		    //	These pins are monitored by this program for keying
		    result = (	(GPIO_KeyerDIT_line = openLineForInput(GPIO_KeyerDIT, true))
				 	&&	(GPIO_KeyerDAH_line = openLineForInput(GPIO_KeyerDAH, true))
				 	&&	(GPIO_PTTIn_line 	= openLineForInput(GPIO_PTTIn, true))
					);
			if (!result)
				perror("Requesting line(s) as input failed\n");
			}				
		}
	
	if (result)
		{
		//	disable the Hat's TX mixer and enable the RX mixer
		result = (	(gpiod_line_set_value(GPIO_notTX_line,1) >= 0)
				&&	(gpiod_line_set_value(GPIO_notRX_line, 0) >= 0)
				);
		if (!result)
			perror("Setting output lines failed\n");
		}

	if (!result && gChip)
		gpiod_chip_close(gChip);
	return result;
}

#endif	// USE_ALL_GPIO

/*
*****************************************************************************
*	mcp 23008/17 I2C gpio port expander support
*
*	This has to handle several different cases:
*	1. Legacy board controlling BOTH lpf and pf from mcp23017
*	2. Legacy board controlling ONLY lpf
*	3. RH2 controlling pf, legacy board controlling lpf
*	4. RH2 controlling pf, new 23008 board controlling LPF
*	5. NO expander devices found at all!
*
*
*****************************************************************************/
const char * kI2CBUS = "/dev/i2c-1";	// Pi user i2c device name

//	MCP23008 is 8 bit and has only one GPIO
const int kMCP23008_0 = 0x21;		//	the expander usually controlling PF
const int kMCP23008_1 = 0x22;		//	the expander usually controlling LPF
const int kIODIR = 0x00;
const int kIOCON = 0x05;
const int kGPIO = 0x09;
const int kOLAT = 0x0a;

//	the MCP23017 is 16 bit with GPIOA and GPIOB
//	this is the default address for most modular expander boards
//	these asssume default IOCON.BANK setting (0)
const int kMCP23017_0 = 0x20;		//	the legacy expander used for both PF and LPF
const int kIODIRA = 0x00;
const int kIODIRB = 0x01;
//const int kIOCON = 0x05;			//	already correctly defined above
const int kGPIOA = 0x12;
const int kGPIOB = 0x13;
const int kOLATA = 0x14;
const int kOLATB = 0x15;


//	Note that the IOCON register controls port mapping and so
//	is always at the same address regardless of device type
//	Access it via the constant "kIOCON" instead of via a global pointer.

//	global port info for accessing the Prefilter port extender (if found)
int gPfFD = 0;
int gPfIODIR = 0;
int gPfGPIO = 0;
int gPfOLAT = 0;

//	global port info for accessing the LPF port extender (if found)
int gLpfFD = 0;
int gLpfIODIR = 0;
int gLpfGPIO = 0;
int gLpfOLAT = 0;


//	the Linux I2C system driver uses the first byte in the buffer it is sent
//	as the destination register pointer to send to the I2C device!
int writeI2CGPIO(int theFD, uint8_t addr, uint8_t data)
{
uint8_t buf[2];
int result = 0;

	if (theFD)
		{
		buf[0]=addr; buf[1]=data;
		result = write(theFD, buf, 2);
		result = (result < 0) ? 0 : 1;
		}
	return result;
}

//	the Linux I2C system driver uses the first byte in the buffer it is sent
//	to as the source register pointer to send to the I2C device!
//	This code doesn't work right - it can't detect read fail of nonexistent i2c device!
int readI2CGPIO(int theFD, uint8_t addr)
{
	uint8_t reg_val = -1;
	uint8_t buf[2];
	buf[0] = addr;

	if (theFD)
		{
		if ((write(theFD, buf, 1) >= 0) && ((read(theFD, buf, 1)) >= 0))
			reg_val = buf[0];
		}
	if (reg_val < 0)
		perror("fail in readI2CGPIO\n");
	return reg_val;
}

//	note that success opening the linux driver IOCTL doesn't mean the target exists!
//  We need to try a write from it as well. There doesn't seem to be a way to do
//	this using reads (at least for these devices)
int openI2CGPIO(int * theFD, int busaddr)
{
	// Start I2C comms
   int reg_val = false;
   if (		((*theFD = open(kI2CBUS, O_RDWR)) >= 0)
   		&&	(ioctl(*theFD, I2C_SLAVE, busaddr & 0xff) >= 0) 
   		&&  (write(*theFD,0,0) >= 0)
	  )
   		reg_val = true;
   	else
   		*theFD = 0;
	return reg_val;
}


//	simply sets or clears one bit in the passed 8 bit extender port
int setRelay(int theFD, int theRelay, int theGPIO, int theOLAT, bool value)
{
int portvalue = readI2CGPIO(theFD, theOLAT);

	if (portvalue < 0)
		return portvalue;
	else {
		portvalue &= 0X00FF;
		if (value) portvalue |= (1 << theRelay);
		else portvalue &= (~( 1 << theRelay) & 0x00FF);
		return (writeI2CGPIO(theFD, theGPIO, portvalue) != 0);
		}
}


//	relay 0 is a reset line to all the latching relays
//	relays 1-7 are mutually exclusive latching relays and must be pulsed
//	this always tries to clear the relay bit, even if the set operation fails
//	All the latching relays are usually on port A.
int pulseRelay(int theFD, int theGPIO, int theOLAT, int theRelay)
{
int result = false;
int result2 = false;

	result = setRelay(theFD, theRelay, theGPIO, theOLAT, true);
	usleep(5000);
	result2 = setRelay(theFD, theRelay, theGPIO, theOLAT, false);

	return result && result2;
}

//	writes all relay bits at once without disturbing other bits
int writeLPFRelays(int theFD, int theOLAT, int theGPIO, uint8_t byteval)
{
	if (theFD == 0)
		return true;
	else
		{
		int portvalue = readI2CGPIO(theFD, theOLAT);

		if (portvalue < 0)
			return portvalue;
		else {
			portvalue &= 0xFFE0;		//	zero the relay bits
			portvalue |= (byteval & 0x001f);
			return (writeI2CGPIO(theFD, theGPIO, portvalue) != 0);
			}
		}
}



/*****************************************************************************
*	support functions for QRP labs filter board
*
*	Note that the QRP labs filter board has funny wiring for filter 1.
*	It is DISABLED by activating the coil! (I think - it's confusing!)
****************************************************************************/
void checkRelays(uint32_t frequency, bool nocache)
{
const uint32_t LPF1_LIMIT = 30000000L;
const uint32_t LPF2_LIMIT = 25000000L;
const uint32_t LPF3_LIMIT = 14500000L;
const uint32_t LPF4_LIMIT = 7500000L;
const uint32_t LPF5_LIMIT = 4000000L;

const uint32_t PRE1_LIMIT = 18500000L;
const uint32_t PRE2_LIMIT = 10500000L;
const uint32_t PRE3_LIMIT = 5600000L;

int theLPfilter;
int thePREfilter;
static int lastLPfilter = -1;
static int lastPREfilter = -1;

		if (frequency < LPF5_LIMIT)			theLPfilter = 0x10;
		else if (frequency < LPF4_LIMIT)	theLPfilter = 0x08;
		else if (frequency < LPF3_LIMIT)	theLPfilter = 0x04;
		else if (frequency < LPF2_LIMIT)	theLPfilter = 0x02;
		else theLPfilter = 0x01;
		if (nocache || (lastLPfilter != theLPfilter))
			{
			writeLPFRelays(gLpfFD, gLpfOLAT, gLpfGPIO, theLPfilter & 0x001f);
			lastLPfilter = theLPfilter;
			}
	
		if (frequency < PRE3_LIMIT)			thePREfilter = 1;
		else if (frequency < PRE2_LIMIT)	thePREfilter = 2;
		else if (frequency < PRE1_LIMIT)	thePREfilter = 3;
		else thePREfilter = 0;
		if (nocache || (lastPREfilter != thePREfilter))
			{
			pulseRelay(gPfFD, gPfGPIO, gPfOLAT, 0);
			pulseRelay(gPfFD, gPfGPIO, gPfOLAT, thePREfilter);
			lastPREfilter = thePREfilter;
			}
}

void setRelayTXANT(bool txOn)
{	setRelay(gLpfFD,7,gLpfGPIO, gLpfOLAT, txOn);	//	in case relay on lpf board
	setRelay(gPfFD, 7,gLpfGPIO, gLpfOLAT, txOn);	//	in case relay on pf board
}

void setRelayPwramp(bool pwrampOn)
{	setRelay(gLpfFD,6, gLpfGPIO, gLpfOLAT, pwrampOn);  }


//	these have no connectors or buffers, but they're included to allow
//	experimentation with controlling the Radiohat board from I2C as well.
//	Note that the mixer enables are active LOW!
void setRelayTXMixer(bool txMixerOn)
{	setRelay(gPfFD, 6, gPfGPIO, gPfOLAT, ! txMixerOn);  }

void setRelayRXMixer(bool rxMixerOn)
{	setRelay(gPfFD, 5, gPfGPIO, gPfOLAT, ! rxMixerOn);  }



int initRelays(void)
{
int result = false;

	//	if RH2 pf is present, set it as PF controlling device
	if (	(openI2CGPIO(&gPfFD, kMCP23008_0) != 0)
		&&	(writeI2CGPIO(gPfFD, kIOCON,0) != 0)	//	Global config register
		&&	(writeI2CGPIO(gPfFD, kIODIR,0) != 0)	//	dir registers all to output
		&&	(writeI2CGPIO(gPfFD, kGPIO,0) != 0)
		)
		{
		gPfIODIR = kIODIR;
		gPfGPIO = kGPIO;
		gPfOLAT = kOLAT;
		result = true;
		}

	//	if a second mcp20008 is found set it as LPF controlling device
	if (	(openI2CGPIO(&gLpfFD, kMCP23008_1) != 0)
		&&	(writeI2CGPIO(gLpfFD, kIOCON, 0) != 0)	//	Global config register
		&&	(writeI2CGPIO(gLpfFD, kIODIR, 0) != 0)	//	dir registers all to output
		&&	(writeI2CGPIO(gLpfFD, kGPIO, 0) != 0)
		)
		{
		gLpfIODIR = kIODIR;
		gLpfGPIO = kGPIO;
		gLpfOLAT = kOLAT;
		result = true;
		}


//	if one or the other is not found, look for a legacy mc23017
//	and if found, install it for either or both
//	(the globals are already preset properly an mcp23017)
	if ((gLpfFD == 0) || (gPfFD == 0))
		{
		int tempFD = 0;
		if (	(openI2CGPIO(&tempFD, kMCP23017_0) != 0)
			&&	(writeI2CGPIO(tempFD, kIOCON,0) != 0)	//	Global config register
			&&	(writeI2CGPIO(tempFD, kIODIRA,0) != 0)	//	dir registers all to output
			&&	(writeI2CGPIO(tempFD, kIODIRB,0) != 0)
			&&	(writeI2CGPIO(tempFD, kGPIOA,0) != 0)
			&&	(writeI2CGPIO(tempFD, kGPIOB,0) != 0)
			)
			{
			printf("found mcp23017\n");
			if (gLpfFD == 0)
				{
				gLpfFD = tempFD;
				gLpfIODIR = kIODIRB;
				gLpfGPIO = kGPIOB;
				gLpfOLAT = kOLATB;
				}
			if (gPfFD == 0)
				{
				gPfFD = tempFD;
				gPfIODIR = kIODIRA;
				gPfGPIO = kGPIOA;
				gPfOLAT = kOLATA;
				}
			result = true;
			}
		}

	//	reset any latching relays to known state
	if (result && gPfFD)
		pulseRelay(gPfFD, gPfGPIO, gPfOLAT, 0);

	if (result)
		checkRelays(28000000L, true);
	else
		perror("Open relay drivers failed\n");
	return result;
}

int uninitRelays(void)
{
	if (gPfFD)
		{
		writeI2CGPIO(gPfFD, gPfGPIO, 0);
		close(gPfFD);
		}
	if (gLpfFD)
		{
		writeI2CGPIO(gLpfFD, gLpfGPIO, 0);
		close(gLpfFD);
		}
	return true;
}




/*
*****************************************************************************
*	TX / RX Switching
****************************************************************************/

//	temporary straight key hack for quisk until CW mode is cleaned up
int isKeyInputActive(void)
{
	return !gpioRead(GPIO_KeyerDAH_line);
}


//	single point to poll for external PTT requests
bool isTXRequested(void)
{
#ifdef USE_ALL_GPIO
bool request = !gpioRead(GPIO_PTTIn_line)
#else
bool request = !gpioRead(GPIO_PTTIn_line);
#endif
	return request;
}

//	hardware TX-RX switching handler, also calls audio switch handler
void enableTX(bool txon, cAudioMode mode)
{
static float savedDACVol= -1;	//	must restore this because modulator may need to
								//	change it and it is needed by built-in audio
								//	output when receiving

	savedDACVol = getDACVol();
	setDACVol(0);						//	to prevent a click

	if (txon)
		{
#ifdef USE_ALL_GPIO
		gpioWrite(GPIO_TXRXRelay_line, 1);
#endif
		gpioWrite(GPIO_notRX_line, 1);
		gpioWrite(GPIO_notTX_line, 0);

#ifdef USE_ALL_GPIO
		gpioWrite(GPIO_PWRAMP_ON_line, 1);
#endif
		setRelayTXANT(true);
		setRelayPwramp(true);
		setRelayTXMixer(true);
		setRelayRXMixer(false);
		setDACVol(savedDACVol);		
		enableTXAudio(txon, mode);
		}
	else
		{
		enableTXAudio(txon, mode);
		setRelayTXMixer(false);
		setRelayPwramp(false);
		setRelayTXANT(false);
		setRelayRXMixer(true);
		
#ifdef USE_ALL_GPIO
		gpioWrite(GPIO_PWRAMP_ON_line, 0);
		gpioWrite(GPIO_TXRXRelay_line, 0);
#endif

		gpioWrite(GPIO_notTX_line, 1);
		gpioWrite(GPIO_notRX_line,  0);
		}	
	setDACVol(savedDACVol);
}

void checkKeydown(void)
{
static bool keyed;

	if (!gpioRead(GPIO_KeyerDAH_line))
		{								//	key IS down
		usleep(1000);
		if(!keyed)						//	key WAS NOT down
			{
			enableTX(true,CW_AUDIO);	//	TX, disable microphone & turn on sidetone
			keyed = true;				//	remember that we are keyed
			}
		}
	else
		{								//	Key IS NOT down
		usleep(1000);
		if (keyed)						//	key WAS down
			{
			enableTX(false,CW_AUDIO);	//	not -digital, so AGC is re-enabled
			keyed = false;				//	remember that we are NOT keyed			
			}
		}
}

	//	at startup, LPF is set to 10 meters
	//	rx is enabled and tx and power amp are disabled
int initControl(void)
{
int result;
	result = (	(initGPIO() == true)
			&&	(initRelays() == true)	);
	if (result)
		enableTX(false, NORMAL_AUDIO);
	else perror("libradiohat:initControl failed");
//	printf("expander globals: \n%i, %i, %i, %i,\n%i, %i, %i %i\n", 
//		gPfFD, gPfIODIR, gPfGPIO, gPfOLAT,gLpfFD,gLpfIODIR,gLpfGPIO,gLpfOLAT);
	return result;
}

void uninitControl(void)
{
	uninitRelays();
	if (gChip)
		gpiod_chip_close(gChip);
}


void checkLPF(uint32_t frequency, bool nocache)
{
	checkRelays(frequency, nocache);
	
#ifdef USE_ALL_GPIO
	checkLPF_GPIO(frequency, nocache);
#endif

}

