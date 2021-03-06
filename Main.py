# sudo apt install python-smbus mplayer python-pip python-dev build-essential pulseaudio
# sudo pip install RPLCD adafruit-pca9685 unidecode pyalsaaudio

import time
from Radio import *
from MyIO import *
import Queue
import threading
import socket


class Main:
    def radio_callback_playing(self):
        MyIO.Radio.set_playing(self.radio.now_playing)
        
    def __init__(self):
        MyIO.setup()
        MyIO.HDMI.setup()

        self.mcu_q = Queue.Queue(maxsize=0)
        self.mcu_thread = threading.Thread(target=self.mcu_listener)
        self.mcu_thread.start()
        MyIO.MCU.setup(event_q=self.mcu_q)

        MyIO.Amp.set_volume(50)

        self.radio = Radio(self.radio_callback_playing)
        MyIO.Radio.set_station(self.radio.get_station()[1])

        MyIO.set_mode(MyIO.Mode.RADIO)
        self.radio.play()

    def mcu_listener(self):
        while True:
            event_type, data = self.mcu_q.get()
            if event_type == MyIO.Command.BUTTON:
                btn_num, state = data
                if btn_num == MyIO.Button.MUTE.value:
                    if state:
                        MyIO.Amp.set_mute()
                elif btn_num == MyIO.Button.PLAY.value:
                    if state:
                        self.radio.play()
                elif btn_num == MyIO.Button.STOP.value:
                    if state:
                        self.radio.stop()
            elif event_type == MyIO.Command.ENCODER:
                MyIO.Amp.set_volume_rel(data)
            self.mcu_q.task_done()


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
