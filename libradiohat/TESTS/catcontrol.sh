sudo modprobe snd-aloop;
python3 ~/radiohat2/libradiohat/TESTS/vswr.py &
socat -d pty,raw,echo=0 exec:"/home/mvano/radiohat2/libradiohat/transceiver -c",pty,raw,setsid &
~/radiohat2/libradiohat/GRC/usbplus.py --GAIN=1.0
sleep 60
