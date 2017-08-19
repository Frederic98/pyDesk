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
        #self.audio_mixer = alsaaudio.Mixer('PCM')
        
        self.station_index = 3
        self.player = None
        self.now_playing = ''
        self.thread = threading.Thread(target=self.radio_worker)

        self.callback = callback
            
        self.thread.start()

    def radio_worker(self):
        while(True):
            if(self.player is None):
                time.sleep(5)
            else:
                uline = self.player.stdout.readline().decode('UTF-8', 'ignore')
                line = unidecode.unidecode(uline)
                if(line == '' or line is None):
                    break
                if(line[0:8] == 'ICY Info'):
                    info = line[10:-1]
                    [key,value] = info.split('=',1)
                    if(key == 'StreamTitle'):
                        self.now_playing = value[1:-2] #Remove '......';
                        if self.callback is not None:
                            self.callback()
            
    def play(self):
        if(self.player is not None):
            self.stop()
        self.player = subprocess.Popen(['mplayer', '-quiet', '-playlist', self.stations[self.station_index]['source']], stdout=subprocess.PIPE, stdin=subprocess.PIPE)
        
    def stop(self):
        self.player.terminate();
        self.player = None

    def set_station(self, index):
        self.stationIndex = index
        self.stop()
        self.play()
        return self.stations[index]['name']
    def next_station(self):
        if(self.stationIndex + 1 >= len(self.stations)):
            self.changeStation(0)
        else:
            self.changeStation(self.stationIndex+1)
        return self.radio_stationName()
    def prev_station(self):
        if(self.stationIndex - 1 < 0):
            self.changeStation(len(self.stations)-1)
        else:
            self.changeStation(self.stationIndex-1)
        return self.radio_stationName()

    def get_station(self):
        return [self.station_index, self.stations[self.station_index]['name']]

    def audio_mute(self):
        self.audio_mixer.setmute(True)
    def audio_unmute(self):
        self.audio_mixer.setmute(False)
    def audio_audio_togglemute(self):
        self.audio_mixer.setmute(not audio_mixer.getmute()[0])


