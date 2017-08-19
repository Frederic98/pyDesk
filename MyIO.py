import time
import threading
import Queue
from enum import Enum
import atexit
import logging

#IO libs
from RPLCD.i2c import CharLCD
from Adafruit_PCA9685 import PCA9685
import RPi.GPIO as GPIO
import smbus


class MyIO:
    #i2c_lcd = 0x27
    i2c_lcd = 0x3f
    i2c_pwm = 0x00
    i2c_amp = 0x00

    lcd_cols = 20
    lcd_rows = 4
    lcd = CharLCD(i2c_expander = 'PCF8574',
                  address = i2c_lcd,
                  port = 1,
                  cols = lcd_cols,
                  rows = lcd_rows,
                  dotsize = 8,
                  charmap = 'A02',
                  auto_linebreaks = True,
                  backlight_enabled = True)
    pwm_mod = PCA9685(address=0x40,
                      busnum=1)
    
    hdmi_states = [[False, False, True,  False],
                   [False, True,  True,  False],
                   [True,  True,  False, False],
                   [True,  True,  False, True],
                   [True,  True,  True,  True]]
    hdmi_pins = [5,6,12,13]
    hdmi_default = 2

    mcu_int_pin = 20
    mcu_ok_pin = 21
    
    i2cbus = smbus.SMBus(1)
    
    worker_thread = None

    modes= ('', 'RADIO', 'BT', 'HDMI', 'AUX', 'SETTINGS')
    bt_device = ''

    q = Queue.Queue(maxsize=0)

    LOG_FORMAT = '\n%(levelname)s - %(asctime)s\n%(message)s'
    logging.basicConfig(filename = 'MyIO.log',
                        level = logging.DEBUG,
                        format = LOG_FORMAT)
    logger = logging.getLogger()
    
    @classmethod
    def worker_start(cls):
        cls.worker_tread = threading.Thread(target=cls.worker, args=(cls.q,))
        cls.worker_tread.start()
        
    @classmethod
    def worker(cls, q):
        mode = 0
        radio_station = ''
        radio_playing = ['', '']
        try:
            while(True):
                qitem = q.get()
                try:
                    cmd, data = qitem
                    #...General...
                    if cmd == cls.Command.MODE:
                        mode_txt = cls.modes[data]
                        space_padding = len(cls.modes[mode]) - len(mode_txt)
                        while space_padding >= 0:
                            mode_txt = ' ' + mode_txt
                            space_padding = space_padding - 1
                        cls.lcd.cursor_pos = [0, cls.lcd_cols - len(mode_txt)]
                        cls.lcd.write_string(mode_txt)
                        mode = data
                    #...AMP...
                    elif cmd == cls.Command.AMP_VOLUME:
                        data = max(0, min(data, 63))
                        volStr = str(data)
                        while(len(volStr) < 3):
                            volStr = ' ' + volStr
                        cls.lcd.cursor_pos = [3,0]
                        cls.lcd.write_string(volStr)
                        #set volume of amplifier
                        #... data = volume (0...63)
                    elif cmd == cls.Command.AMP_INPUT:
                        #set volume of amplifier
                        #... data = [input num, gain_enable, gain]
                        pass
                    #...Radio...
                    elif cmd == cls.Command.RADIO_STATION:
                        station_txt = data
                        space_padding = len(radio_station) - len(station_txt)
                        radio_station = station_txt
                        while space_padding > 0:
                            station_txt = station_txt + ' '
                            space_padding = space_padding - 1
                        station_txt = station_txt[0:cls.lcd_cols - len(cls.modes[mode]) - 2]
                        cls.lcd.cursor_pos = [0, 1]
                        cls.lcd.write_string(station_txt)
                    elif cmd == cls.Command.RADIO_PLAYING:
                        playing_txt = data
                        while len(radio_playing[0]) - len(playing_txt[0]) > 0:
                            playing_txt[0] = playing_txt[0] + ' '
                        while len(radio_playing[1]) - len(playing_txt[1]) > 0:
                            playing_txt[1] = playing_txt[1] + ' '
                        radio_playing = playing_txt
                        playing_txt[0] = playing_txt[0][0:20]
                        playing_txt[1] = playing_txt[1][0:20]
                        cls.lcd.cursor_pos = [1, 0]
                        cls.lcd.write_string(playing_txt[0])
                        cls.lcd.cursor_pos = [2, 0]
                        cls.lcd.write_string(playing_txt[1])
                    #...PWM...
                    elif cmd == cls.Command.PWM_SET_CHANNEL:
                        cls.pwm_mod.set_pwm(data[0], data[1], data[2])
                    elif cmd == cls.Command.PWM_SET_FREQ:
                        cls.pwm_mod.set_pwm_freq(data)
                    #...HDMI...
                    elif cmd == cls.Command.HDMI_SETUP:
                        GPIO.setmode(GPIO.BCM)
                        GPIO.setup(cls.hdmi_pins, GPIO.OUT)
                        cls.HDMI.set_source(cls.hdmi_default)
                    elif cmd == cls.Command.HDMI_SET_SOURCE:
                        GPIO.output(cls.hdmi_pins, cls.hdmi_states[data])
                    #...MCU IO...
                    elif cmd == cls.Command.MCU_SETUP:
                        GPIO.add_event_detect(cls.mcu_int_pin, GPIO.BOTH)
                        GPIO.add_event_callback(cls.mcu_int_pin, cls.MCU.event_callback)
                    elif cmd == cls.Command.MCU_GET:
                        try:
                            data = cls.i2cbus.read_i2c_block_data(0x08, 0, 4)
                            cls.MCU._receive_q.put([1, data])
                        except Exception as e:
                            cls.MCU._receive_q.put([0, e])
                    elif cmd == cls.Command.MCU_SET_OK:
                        GPIO.output(cls.mcu_ok_pin, data)
                except Exception as e:
                    cls.logger.error('Exception occurerd while executing IO command\nQueue item = ' + str(qitem) + '\n' + repr(e))
                q.task_done()
        except (SystemExit, KeyboardInterrupt) as e:
            GPIO.cleanup()

    @classmethod
    def set_mode(cls, m):
        cls.q.put([cls.Command.MODE, m])

    @classmethod
    def register_exit(cls):
        atexit.register(cls.exit_handler)

    @classmethod
    def exit_handler(cls):
        GPIO.cleanup()

    class Radio:
        station = ''
        playing = ''

        @classmethod
        def set_station(cls, s):
            cls.station = s
            MyIO.q.put([MyIO.Command.RADIO_STATION, s])

        @classmethod
        def set_playing(cls, p):
            cls.playing = p.split(' - ', 1)
            while len(cls.playing) < 2:
                cls.playing.append('')
            MyIO.q.put([MyIO.Command.RADIO_PLAYING, cls.playing])

    class PWM:
        duty = [0 for i in range(16)]
        freq = 0

        @classmethod
        def set_duty(cls, c, n):
            cls.duty[c] = n % (2**12)
            MyIO.q.put([MyIO.Command.PWM_SET_CHANNEL, [c, 0, n]])

        @classmethod
        def set_freq(cls, f):
            cls.freq = f
            MyIO.q.put([MyIO.Command.PWM_SET_FREQ, f])

    class Amp:
        volume = 0
        input_num = 0
        input_gain = 0
        input_gain_enable = False

        @classmethod
        def set_volume(cls, v):
            cls.volume = v
            MyIO.q.put([MyIO.Command.AMP_VOLUME, v])

        @classmethod
        def set_input(cls, n):
            cls.set_input(n, False, 0)

        @classmethod
        def set_input(cls, n, gain_en, gain):
            cls.input_num = n
            cls.input_gain_enable = gain_en
            cls.input_gain = gain
            MyIO.q.put([MyIO.Command.AMP_INPUT, [n, gain_en, gain]])

    class HDMI:
        active_source = 0

        @classmethod
        def setup(cls):
            MyIO.q.put([MyIO.Command.HDMI_SETUP, 0])

        @classmethod
        def set_source(cls, n):
            cls.active_source = n % len(MyIO.hdmi_states)
            MyIO.q.put([MyIO.Command.HDMI_SET_SOURCE, cls.active_source])

        @classmethod
        def next_source(cls):
            cls.set_source(cls.active_source + 1)

        @classmethod
        def prev_source(cls):
            cls.set_source(cls.active_source - 1)
            
    class MCU:
        buttons = [False for n in range(16)]
        encoder = 0
        _receive_q = Queue.Queue(maxsize=0)

        @classmethod
        def setup(cls):
            cls.worker_thread = threading.Thread(target=cls.response_listener)
            cls.worker_thread.start()
            MyIO.q.put([MyIO.Command.MCU_SETUP, 0])

        @classmethod
        def get_states(cls):
            MyIO.q.put([MyIO.Command.MCU_GET, 0])

        @classmethod
        def response_listener(cls):
            while(True):
                state, data = cls._receive_q.get()
                if state == 1:
                    button_states = (data[1] << 8) | data[2]
                    n_buttons_pressed = 0
                    new_button_states = [False for n in range(16)]
                    for i in range(16):
                        if ((button_states >> i) & 0x01) > 0:
                            n_buttons_pressed += 1
                            new_button_states[i] = True
                    if n_buttons_pressed != data[3]:
                        cls.get_states()
                    else:
                        cls.buttons = new_button_states
                    if data[0] > 127:
                        data[0] = data[0] - 256
                    encoder = data[0]
                    MyIO.q.put([MyIO.Command.MCU_SET_OK, True])
                else:
                    cls.get_states()
                cls._receive_q.task_done()

        @classmethod
        def event_callback(cls, channel):
            if GPIO.input(channel) == GPIO.HIGH:
                cls.get_states()
            else:
                MyIO.q.put([MyIO.Command.MCU_SET_OK, False])
            
    class Command(Enum):
        MODE = 1
        
        RADIO_STATION = 101
        RADIO_PLAYING = 102

        BT_CONNECTED = 201
        BT_DEVICE = 202

        AMP_VOLUME = 501
        AMP_INPUT = 502

        PWM_SET_CHANNEL = 601
        PWM_SET_ALL = 602
        PWM_SET_FREQ = 603

        HDMI_SETUP = 701
        HDMI_SET_SOURCE = 702

        MCU_SETUP = 801
        MCU_GET = 802
        MCU_SET_OK = 803

    class Mode(Enum):
        OFF = 0
        RADIO = 1
        BT = 2
        HDMI = 3
        AUX = 4
        SETTINGS = 5

MyIO.worker_start()
MyIO.register_exit()
