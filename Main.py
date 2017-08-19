'''
sudo apt install python-smbus mplayer python-pip python-dev build-essential pulseaudio
sudo pip install RPLCD adafruit-pca9685 unidecode
'''

import time
from Radio import *
from MyIO import *

class Main:
    def radio_callback_playing(self):
        MyIO.Radio.set_playing(self.radio.now_playing)
        
    def __init__(self):
        self.radio = Radio(self.radio_callback_playing)
        MyIO.set_mode(MyIO.Mode.RADIO)
        MyIO.Radio.set_station(self.radio.get_station()[1])
        MyIO.HDMI.setup()

        self.radio.play() 

import socket
def internet(host="8.8.8.8", port=53, timeout=3):
    """
    Host: 8.8.8.8 (google-public-dns-a.google.com)
    OpenPort: 53/tcp
    Service: domain (DNS/TCP)
    """
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        return True
    except Exception as ex:
        print(ex.message)
        return False

while not internet():
    pass
m=Main()
