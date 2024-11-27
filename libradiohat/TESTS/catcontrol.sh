YOUR_HOME=/home/mvano
RADIOHAT=$YOUR_HOME/radiohat2
sudo modprobe snd-aloop
python $RADIOHAT/libradiohat/TESTS/vswr.py &
socat -d pty,raw,echo=0 exec:"/home/mvano/radiohat2/libradiohat/transceiver -c",pty,raw,setsid &
$RADIOHAT/libradiohat/GRC/usbplus.py --GAIN=0.4
sleep 100


