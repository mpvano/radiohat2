![3dView](radiohead2.jpg?raw=true "Title")
# RadioHat 2

This is an early version of the folder full of files that need to be installed on a raspberry pi to allow experimentation with the RadioHat version 2.0 hardware.

When downloading and installing it, ensure that it is named "radiohat2" and that it is in your home directory, or some of the shell scripts it contains will not work properly. When downloaded as a .zip archive, it may result in a folder with the branch suffix "-main" that needs to be removed if you want to use the enclosed shell scripts.

One way to create the folder on a pi is to "cd" to the directory you want it to appear in and then clone the repository using git with the command: "git clone https://github.com/mpvano/radiohat2.git". This will allow you to use all the normal git functionality.

Note also that some of the files in "docs" are very out of date or incomplete. The "Getting Started Guides" refer to a much earlier configuration with different directories on the pi and procedures to set things up. They're presented here only to give some idea what to do. I'll be replacing them with more modern versions as I get to them. RadioHat is still very much a work in progress.

### The RadioHat hardware

Unlike RadioHat 1, RadioHat2 is an open source peripheral board for the Raspberry Pi in a form similar to an extended Pi "hat". Note that this board overhangs the pi USB and Ethernet connectors to match the dimensions of the Pi itself. This means it does not qualify as an official "HAT". It is intended to be a module containing many of the devices that are commonly needed to implement 3-30Mhz radio transmitters and receivers. It may also be used with other micro-controllers that support I2S if they are sufficiently powerful to handle the needed DSP operations.

It contains the following devices:<ol>
	<li>A Freescale SGTL5000 24 bit full duplex 48Khz I2S Audio codec with headset interface</li>
	<li>A Quadrature Switched Demodulator preceded by a 3-32Mhz Band Pass Filter</li>
	<li>A Quadrature Switched Modulator followed by a 32Mhz Low Pass Filter</li>
	<li>An Si5351 I2C controlled clock oscillator configured to provide quadrature clocks for them</li>
	<li>The EEPROM required by the Pi Foundation for "hat" devices</li>
	<li>Three relay controlled low pass filters intended for use after the Modulator to reduce harmonics before an external power amplifier.</li>
 	<li>A Class A Predriver to improve the Modulator drive capabilities and to compensate for filter losses.</li>
	<li>On board analog regulators to provide cleaner power from an optional external source</li>
</ol>

These devices are wired together in the usual way needed for HF radio operation with DSP provided by the Raspberry Pi. For typical operation as a radio transceiver you still need to provide a power amplifier with output filters and a transmit/receive switching mechanism. The usual output low pass filters are adequate for most uses as input filters for the receiver if the T/R switching is done in such a way that they remain inline with the receiver.

The repository now contains another board design of the same size in FAB/txfilters1 which implements a 5 filter LPF/VSWR Meter/TR Relay for stacking with the RadioHat board. Together with your choice of power amplifier this now allows a complete transceiver to be built easily.

Note that the real time clock option and Codec Line input output connection points that were present in Radiohat 1 have been removed. The Radiohat 1 board whose Kicad Folder is still in the repository remains software compatible with this board and although it is no longer under development it remains a viable option for those needing a true "hat" for the pi, or requiring a real time clock. 

There are two different Kicad folders available for RadioHat 2 - they differ primarily in that the one named "radiohat2_QFP32" is compatible with older 32 pin versions of the codec chip instead of the current 20 pin part. They will eventually be merged into a single version.

### Fabrication of boards
RadioHat2 is open sourced hardware licensed via an MIT license and the Gerber files, preliminary BOM and some draft documentation are all part of the project. 

Although a small production run was completed to provide a few boards for use by software developers, there is currently no way to obtain boards other than ordering them from a board manufacturer yourself - this is easy and inexpensive to do and the needed Gerber files are in this repository.

Note that this board is very compact and built with QFPn and 0603 components. It's not very practical to attempt assembly by hand. The board is intended to be reflow soldered after the components are placed on pads with the help of a front side solder paste screen.

### Software
The provided software is a collection of example and test programs that demonstrate operation of the board and allow testing and troubleshooting of it. They are only intended as a starting point for more serious software development. Experimental support is also provided for use with the popular "Quisk" Transceiver software as well.

This repository is newly setup and is still being tested. There may be some issues with missing files, etc. They are being addressed as quickly as possible.

### Dependencies
In general they are confined to the normal Raspberry Pi build tools, with the exception of ncurses and its development tools.

There is a simple installation described in the PDF file in the DOC folder.

Version 7 of Kicad or later is needed to modify the board design.

### Mailing list

There is a moderated mailing list for discussing this project at https://groups.io/g/RadioHat. This project's goal is develop radio equipment that requires a valid radio amateur operator's license to operate. Please include your valid station call sign in requests to join the list, and the nature of your interest in the project.

Mario Vano
AE0GL
