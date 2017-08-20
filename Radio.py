import time
import subprocess
import sys
import threading
import unidecode


class Radio:
    stations = [
        {
            'name':    'NPO Radio 2',
            'source':  'http://icecast.omroep.nl/radio2-bb-mp3.m3u'
        },
        {
            'name':    '3FM',
            'source':  'http://icecast.omroep.nl/3fm-bb-mp3.m3u'
        },
        {
            'name':    '538',
            'source':  'http://vip-icecast.538.lw.triple-it.nl/RADIO538_MP3.m3u'
        },
        {
            'name':    'Q-Music',
            'source':  'http://icecast-qmusic.cdp.triple-it.nl/Qmusic_nl_live_96.mp3.m3u'
        }
    ]
    
    def __init__(self, callback=None):
        self.station_index = 3
        self.player = None
        self.player_active = False
        self.now_playing = ''
        self.thread = threading.Thread(target=self.radio_worker)

        self.callback = callback
            
        self.thread.start()

    def radio_worker(self):
        while True:
            if self.player is None:
                time.sleep(5)
            else:
                uline = self.player.stdout.readline().decode('UTF-8', 'ignore')
                line = unidecode.unidecode(uline)
                if line == '' or line is None:
                    break
                if line[0:8] == 'ICY Info':
                    info = line[10:-1]
                    [key, value] = info.split('=', 1)
                    if key == 'StreamTitle':
                        self.now_playing = value[1:-2]
                        if self.callback is not None:
                            self.callback()
            
    def play(self):
        if self.player is not None or self.player_active:
            self.stop()
        self.now_playing = chr(0)
        self.callback()
        self.player = subprocess.Popen(['mplayer', '-quiet', '-playlist', self.stations[self.station_index]['source']],
                                       stdout=subprocess.PIPE,
                                       stdin=subprocess.PIPE)
        self.player_active = True
        
    def stop(self):
        if self.player is not None:
            self.player.terminate()
            self.player = None
        self.player_active = False
        self.now_playing = ''
        self.callback()

    def set_station(self, index):
        self.station_index = index
        self.stop()
        self.play()
        return self.stations[index]['name']

    def next_station(self):
        if self.station_index + 1 >= len(self.stations):
            self.set_station(0)
        else:
            self.set_station(self.station_index + 1)
        return self.get_station()

    def prev_station(self):
        if self.station_index - 1 < 0:
            self.set_station(len(self.stations)-1)
        else:
            self.set_station(self.station_index - 1)
        return self.get_station()

    def get_station(self):
        return [self.station_index, self.stations[self.station_index]['name']]
