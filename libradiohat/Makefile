all:	transceiver libradiohat.so radiohatcodec/radiohatcodec.dtbo

transceiver: transceiver.cpp libradiohat.so
	c++ transceiver.cpp -o transceiver -lncurses -L. -lradiohat -Wl,-rpath,/home/pi/radiohat/libradiohat

libradiohat.so:	codec.cpp control.cpp si5351pi.cpp vfo.cpp vswr.cpp *.h
	c++ -c -fPIC control.cpp codec.cpp si5351pi.cpp vfo.cpp vswr.cpp
	c++ -shared control.o codec.o si5351pi.o vfo.o vswr.o -o libradiohat.so -L. -lgpiod 

radiohatcodec/radiohatcodec.dtbo:	radiohatcodec/radiohatcodec.dts
	dtc -@ -H epapr -O dtb -o radiohatcodec/radiohatcodec.dtbo -Wno-unit_address_vs_reg radiohatcodec/radiohatcodec.dts

clean:
	rm -f *.o *.so transceiver CONFIG_CACHE*
	rm -f radiohatcodec/radiohatcodec.dtbo

install:
	cp libradiohat.so /usr/lib/libradiohat.so
	ldconfig
	cp radiohatcodec/radiohatcodec.dtbo /boot/overlays
	rm -f CONFIG_CACHE*
	echo "\n[all]\n##RadioHat 1.0##" > CONFIG_CACHE_HEAD
	echo "\n[all]" > CONFIG_CACHE_TAIL
	if ! grep -q "^dtparam=i2c.*=on" /boot/config.txt ; then echo "dtparam=i2c=on";  fi >> CONFIG_CACHE_BODY
	if ! grep -q "^dtparam=i2s=on" /boot/config.txt ; then echo "dtparam=i2s=on";  fi >> CONFIG_CACHE_BODY
	if ! grep -q "^dtoverlay=RadioHatCodec" /boot/config.txt ; then echo "dtoverlay=RadioHatCodec";  fi >> CONFIG_CACHE_BODY
	if ! grep -q "^gpio=22,23=op,dh" /boot/config.txt ; then echo "gpio=22,23=op,dh";  fi >> CONFIG_CACHE_BODY
	if test -s CONFIG_CACHE_BODY ; then cat CONFIG_CACHE_HEAD CONFIG_CACHE_BODY CONFIG_CACHE_TAIL ; fi >> /boot/config.txt

remove:
	rm /usr/lib/libradiohat.so
	rm /boot/overlays/radiohatcodec.dtbo
