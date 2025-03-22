import time
from machine import Pin, I2C,time_pulse_us,PWM,ADC
import neopixel

class iic_base:
    def __init__(self):
        # 初始化 I2C
        self.i2c = I2C(1, sda=Pin(7), scl=Pin(8), freq=100000)
    
    def write_bytes(self,addr,data):
        try:
            self.i2c.writeto(addr, bytes(data),True)
        except OSError as e:
            print("I2C Write Error:", e)

    def read_bytes(self,addr,length):
        try:
            return self.i2c.readfrom(addr, length,True)
        except OSError as e:
            print("I2C Read Error:", e)
            return bytes([0] * length)
   
    def is_ready(self,addr): # 是否在线
        try:
           self.read_bytes(addr,1)
        except:
            return 0
        return 1
i2c =  iic_base()
# 伺服电机
class servo_motor:
    GENERAL      = 0x50  # 通用地址
    LIGHT_RED    = 0x51  # 红灯
    LIGHT_GREEN  = 0x52  # 绿灯
    LIGHT_BLUE   = 0x53  # 蓝灯
    LIGHT_YELLOW = 0x54  # 黄灯
    def __init__(self,addr:int):
        self.addr = addr

    def _send_command(self,data:list): # 三个数据
        velocity = data[1]
        data[2] = int(data[2])
        velocity = int(velocity)
        velocity //= 2
        velocity = -50 if velocity<-50 else 50 if velocity > 50 else velocity
        send_data = [data[0]&0xff, velocity&0xff, (data[2]>>8)&0xff, data[2]&0xff]
        i2c.write_bytes(self.addr,send_data)
        
    def _get_data(self):
        data = i2c.read_bytes(self.addr,6)
        ret_data = [data[0], (data[1]<<8)|data[2], (data[3]<<8)|data[4], data[5]]
        return ret_data
        
    def is_end_run(self):
        data = self._get_data()
        cmd = data[3]
        if cmd==0x01 or cmd==0x06:
            return 1
        if cmd==0x00 or cmd==0x0B or cmd==0x0a:
            return 1
        return 0
       
    def run(self,velocity:int): # 以多少的速度运行电机
        self._send_command([0x01, velocity, 0])
        
    def run_for_time(self,velocity, duration, isBlock=True): # 以多少的速度运行多长时间
        if 0 < duration < 0.1:
            duration = 0.1
        duration *= 10
        self._send_command([0x02, velocity, duration])
        if isBlock:
            time.sleep_ms(10)
            while not self.is_end_run():
                pass
    
    def run_to_absolute_position(self, velocity, position, isBlock=True):# 以多少的速度运行到绝对位置
        self._send_command([0x03, velocity, position])
        if isBlock:
            time.sleep_ms(10)
            while not self.is_end_run():
                pass
    
    def run_to_relative_position(self,velocity, position, isBlock=True):# 以多少的速度运行到相对位置
        self._send_command([0x04, velocity, position])
        if isBlock:
            time.sleep_ms(10)
            while not self.is_end_run():
                pass

    def get_absolute_position(self): # 得到电机的绝对位置
        data = self._get_data()
        position = data[1]
        singned_num = 0
        if position >= 0x8000:  # 0x8000 是 32768
            singned_num = position - 0x10000  # 转换为负数
        else:
            singned_num = position
        return singned_num

font =\
(0x0022d422,0x0022d422,0x0022d422,0x0022d422,0x0022d422,0x0022d422,0x0022d422,0x0022d422,0x0022d422,0x0022d422,0x0022d422,0x0022d422,0x0022d422,0x0022d422,0x0022d422,0x0022d422,0x0022d422,
0x0022d422,0x0022d422,0x0022d422,0x0022d422,0x0022d422,0x0022d422,0x0022d422,0x0022d422,0x0022d422,0x0022d422,0x0022d422,0x0022d422,0x0022d422,0x0022d422,0x0022d422,0x00000000,0x000002e0,
0x00018060,0x00afabea,0x00aed6ea,0x01991133,0x010556aa,0x00000060,0x000045c0,0x00003a20,0x00051140,0x00023880,0x00002200,0x00021080,0x00000100,0x00111110,0x0007462e,0x00087e40,0x000956b9,0x0005d629,
0x008fa54c,0x009ad6b7,0x008ada88,0x00119531,0x00aad6aa,0x0022b6a2,0x00000140,0x00002a00,0x0008a880,0x00052940,0x00022a20,0x0022d422,0x00e4d62e,0x000f14be,0x000556bf,0x0008c62e,0x0007463f,0x0008d6bf,
0x000094bf,0x00cac62e,0x000f909f,0x000047f1,0x0017c629,0x0008a89f,0x0008421f,0x01f1105f,0x01f4105f,0x0007462e,0x000114bf,0x000b6526,0x010514bf,0x0004d6b2,0x0010fc21,0x0007c20f,0x00744107,0x01f4111f,0x000d909b,
0x00117041,0x0008ceb9,0x0008c7e0,0x01041041,0x000fc620,0x00010440,0x01084210,0x00000820,0x010f4a4c,0x0004529f,0x00094a4c,0x000fd288,0x000956ae,0x000097c4,0x0007d6a2,0x000c109f,0x000003a0,0x0006c200,0x0008289f,
0x000841e0,0x01e1105e,0x000e085e,0x00064a4c,0x0002295e,0x000f2944,0x0001085c,0x00012a90,0x010a51e0,0x010f420e,0x00644106,0x01e8221e,0x00093192,0x00222292,0x00095b52,0x0008fc80,0x000003e0,0x000013f1,
0x00841080,0x0022d422)

_screen = [0]*1025
_ZOOM = 1

def cmd1(addr,cmd):
    i2c.write_bytes(addr,[0, cmd % 256]) 

def cmd2(addr, cmd1, cmd2):
    _buf = [0, cmd1, cmd2]
    i2c.write_bytes(addr,_buf) 

def cmd3(addr, cmd1, cmd2, cmd3):
    _buf = [0, cmd1, cmd2, cmd3]
    i2c.write_bytes(addr,_buf)

def set_pos(addr, col=0, page=0):
    cmd1(addr, 0xb0 | page) # page number
    c = col * (1 + 1)
    cmd1(addr, 0x00 | (c % 16)) # lower start column address
    cmd1(addr, 0x10 | (c >> 4)) # upper start column address    

def clear_screen(addr):
    for i in range(1024):
        _screen[i] = 0
    set_pos(addr)
    _screen
    _screen[0] = 0x40
    i2c.write_bytes(addr,_screen)

def showStringxy(addr, x, y, s, color = 1):
    col = 0
    e = 0
    ind = 0
    for f in range(len(s)):
        e = font[ord(s[f])]
        for g in range(5):
            col = 0
            for h in range(5):
                if (e & (1 << (5 * g + h))):
                    col |= (1 << (h + 1))
            ind = (x + f) * 5 * (_ZOOM + 1) + y * 128 + g * (_ZOOM + 1) + 1
            if (color == 0):
                col = 255 - col
            _screen[ind] = col
            if (_ZOOM):
                _screen[ind + 1] = col
    set_pos(addr, x * 5, y)
    ind0 = x * 5 * (_ZOOM + 1) + y * 128
    buf7 = _screen[ind0 : ind + 1]
    buf7[0] = 0x40
    i2c.write_bytes(addr,buf7)

def _init(addr):
    # 
    cmd1(addr, 0xAE)       # SSD1306_DISPLAYOFF
    cmd1(addr, 0xA4)       # SSD1306_DISPLAYALLON_RESUME
    cmd2(addr, 0xD5, 0xF0) # SSD1306_SETDISPLAYCLOCKDIV
    cmd2(addr, 0xA8, 0x3F) # SSD1306_SETMULTIPLEX
    cmd2(addr, 0xD3, 0x00) # SSD1306_SETDISPLAYOFFSET
    cmd1(addr, 0 | 0x0)    # line #SSD1306_SETSTARTLINE
    cmd2(addr, 0x8D, 0x14) # SSD1306_CHARGEPUMP
    cmd2(addr, 0x20, 0x00) # SSD1306_MEMORYMODE
    cmd3(addr, 0x21, 0, 127) # SSD1306_COLUMNADDR
    cmd3(addr, 0x22, 0, 63)  # SSD1306_PAGEADDR
    cmd1(addr, 0xa0 | 0x1) # SSD1306_SEGREMAP
    cmd1(addr, 0xc8)       # SSD1306_COMSCANDEC
    cmd2(addr, 0xDA, 0x12) # SSD1306_SETCOMPINS
    cmd2(addr, 0x81, 0xCF) # SSD1306_SETCONTRAST
    cmd2(addr, 0xd9, 0xF1) # SSD1306_SETPRECHARGE
    cmd2(addr, 0xDB, 0x40) # SSD1306_SETVCOMDETECT
    cmd1(addr, 0xA6)       # SSD1306_NORMALDISPLAY
    cmd2(addr, 0xD6, 1)    # zoom on
    cmd1(addr, 0xAF)       # SSD1306_DISPLAYON
    clear_screen(addr)
# 显示屏
class OLED:
    def __init__(self):
        _init(0x3c)
    
    def set_text(self, x, y, text, color=1):
        showStringxy(0x3c, x, y, text, color)

    def clear_screen(self):
        clear_screen(0x3c)

def uigned8_to_signedInt(data:int):
    if data >= 128:
        return data - 256
    else:
        return data
# 摇杆   
class joystick_sensor:
    def __init__(self):
        self.addr = 0x61
    def uigned8_to_signedInt(self,data:int):
        if data >= 128:
            return data - 256
        else:
            return data
    
    def get_x(self): #在x轴的输出值 -100 ~ 100
        data = i2c.read_bytes(self.addr,4)
        return self.uigned8_to_signedInt(data[1])
    
    def get_y(self): #在y轴的输出值 -100 ~ 100
        data = i2c.read_bytes(self.addr,4)
        return self.uigned8_to_signedInt(data[2])
    
    def is_up(self):# 操纵杆是否向上 
        return True if self.get_y()<-50 else False
    
    def is_down(self): # 操纵杆是否向下 
        return True if self.get_y()>50 else False
    
    def is_left(self): # 是否向左
        return True if self.get_x()<-50 else False
    
    def is_right(self): # 是否向右
        return True if self.get_x()>50 else False
# 超声波
class ultrasonic_sensor:
    def __init__(self):
        self.trigpin = Pin(8, Pin.OUT)
        self.echopin = Pin(7, Pin.IN)

    def get(self): #cm
        self.trigpin.value(0)  # 确保Trig引脚为低电平
        time.sleep_us(2)
        self.trigpin.value(1)  # 发送高电平脉冲
        time.sleep_us(10)
        self.trigpin.value(0)  # 结束脉冲
        pulse_time = time_pulse_us(self.echopin, 1, 5000)
        # 计算距离，声速大约为340米每秒，单位转换到厘米
        distance = pulse_time * 34 / 2 / 1000 * 3 / 2  # pulse_time in microseconds, distance in cm
        
        return distance
# 录音
class recording:
    GUNSHOT       = 1 # 枪声
    LASER         = 2 # 激光
    MOTORCYCLE    = 3 # 激光
    WARBEGIN      = 4 # 战争开始
    COUNTDOWN     = 5 # 倒计时
    PLAYRECORDING = 6 # 播放录音

    def voice(self, index:int):
        i2c.write_bytes(0x18,[index])
# 灯环
class light_ring:
    WHITE = 0
    BLACK = 1 # 黑色必须为1；用于灰度黑线判断
    RED   = 2
    ORANGE= 3
    YELLOW= 4
    GREEN = 5
    CYAN  = 6
    BLUE  = 7
    PURPLE= 8
    COLOR_NONE = -1
    def __init__(self):
        self._light = 0.05
        self._handle = neopixel.NeoPixel(Pin(8),9)
        self._color_map = \
        {
            self.BLACK:(0, 0, 0),
            self.BLUE :(0, 0, 255),
            self.COLOR_NONE:(0, 0, 0),
            self.CYAN:(0, 255, 255),
            self.GREEN:(0, 255, 0),
            self.ORANGE:(255, 165, 0),
            self.PURPLE:(128, 0, 128),
            self.WHITE : (255, 255, 255),
            self.RED : (255, 0, 0),
            self.YELLOW : (255, 255, 0)
        }
    def light(self, light): # 设置亮度 0 - 255
        self._light = light/255
        
    def color(self, color):
        # 如果传入的是元组，直接使用
        if isinstance(color, tuple):
            _color = color
        else:
            # 否则，使用预定义的颜色映射
            _color = self._color_map.get(color, (0, 0, 0))  # 默认颜色是黑色

        # 根据亮度调节RGB颜色值
        _color = (int(_color[0] * self._light), int(_color[1] * self._light), int(_color[2] * self._light))

        # 设置NeoPixel灯条的所有像素为指定的颜色
        self._handle.fill(_color)
        self._handle.write()
# led灯
class led:
    def __init__(self):
        self.pwm = PWM(Pin(8), freq=1000, duty=1023)

    def on(self, lum):
        # 将 lum 映射为 0-1023 范围，lum 的有效范围是 0-100
        lum = max(0, min(100, int(lum)))  # 确保亮度在 0-100 之间
        duty_value = 1023 - int(lum * 1023 / 100)  # 映射到 PWM 占空比
        self.pwm.duty(duty_value)

    def off(self):
        # 关闭 LED，设置为灭状态
        self.pwm.duty(1023)
# 激光
class laser:
    def __init__(self):
        self.pwm = PWM(Pin(8), freq=1000, duty=1023)

    def on(self, lum):
        # 将 lum 映射为 0-1023 范围，lum 的有效范围是 0-100
        lum = max(0, min(100, int(lum)))  # 确保亮度在 0-100 之间
        duty_value = int(lum * 1023 / 100)
        self.pwm.duty(duty_value)

    def off(self):
        # 关闭，设置为灭状态
        self.pwm.duty(0)
# 风扇
class fan:
    def __init__(self):
        self.pwm_8 = PWM(Pin(8), freq=1000, duty=0)
        self.pwm_7 = PWM(Pin(7), freq=1000, duty=0)

    def on(self, lum):
        # 将 lum 映射为 0-1023 范围，lum 的有效范围是 0-100
        if lum < 0:
            lum = -lum
            lum = max(0, min(100, int(lum)))  # 确保亮度在 0-100 之间
            duty_value = int(lum * 1023 / 100)
            self.pwm_7.duty(duty_value)
        else:
            lum = max(0, min(100, int(lum)))  # 确保亮度在 0-100 之间
            duty_value = int(lum * 1023 / 100)
            self.pwm_8.duty(duty_value)

    def off(self):
        # 关闭 LED，设置为灭状态
        self.pwm.duty(0)
# 电磁铁
class electromagnet:
    def __init__(self):
        self.pin = Pin(8, Pin.OUT)  # 初始化引脚8为输出模式

    def on(self):
        self.pin.value(1)  # 拉高电平，打开

    def off(self):
        self.pin.value(0)  # 拉低电平，关闭
# 按键
class button:
    def __init__(self):
        self.pin = Pin(8, Pin.IN, Pin.PULL_UP)  # 初始化引脚8为输出模式

    def value(self):
        return self.pin.value()  # 拉高电平，打开

    def is_pressed(self):
        if self.pin.value() == 0:  # 按键按下（低电平）
            time.sleep_ms(100)  # 消抖延时
            if self.pin.value() == 0:  # 再次确认按键是否仍然按下
                return True
        return False
# 气体
class gasConcentration:
    def __init__(self):
        self.adc = ADC(Pin(8))   # create an ADC object acting on a pin
        self.adc.atten(ADC.ATTN_11DB)
    def value(self):
        raw_value = self.adc.read() 
        mapped_value = int((raw_value / 4095) * 1023) 
        return mapped_value
# 远距离光电   
class farState:
    def __init__(self):
        self.pin = Pin(8, Pin.IN) 
    def value(self):
        return self.pin.value()
# 灰度
class graylevel:
    def __init__(self):
        self.adc = ADC(Pin(8))   # create an ADC object acting on a pin
        self.adc.atten(ADC.ATTN_11DB)
    def value(self):
        raw_value = self.adc.read()  
        mapped_value = int((raw_value / 4095) * (1023 - 80) + 80)  # 线性映射到 80-1023
        return mapped_value
# 电位器
class potentiometer:
    def __init__(self):
        self.adc = ADC(Pin(8))   # create an ADC object acting on a pin
        self.adc.atten(ADC.ATTN_11DB)
    def value(self):
        raw_value = self.adc.read() 
        mapped_value = int((raw_value / 4095) * 1023) 
        return mapped_value
# 光敏
class lightintensity:
    def __init__(self):
        self.adc = ADC(Pin(8))   # create an ADC object acting on a pin
        self.adc.atten(ADC.ATTN_11DB)
    def value(self):
        raw_value = self.adc.read() 
        mapped_value = int((raw_value / 4095) * 1023) 
        return 1023 - mapped_value
# 霍尔
class hallsensor:
    def __init__(self):
        self.adc = ADC(Pin(8))   # create an ADC object acting on a pin
        self.adc.atten(ADC.ATTN_11DB)
    def value(self):
        value = self.adc.read()  # 读取 ADC 值（范围 0-4095）
        mapped_value = int((value / 4095) * 1023) 
        return 1 if mapped_value >= 2048 else 0
# 火焰
class flame:
    def __init__(self):
        self.adc = ADC(Pin(8))   # create an ADC object acting on a pin
        self.adc.atten(ADC.ATTN_11DB)
    def value(self):
        raw_value = self.adc.read() 
        mapped_value = int((raw_value / 4095) * 1023) 
        return 1023 - mapped_value
# 防水温度
class watertemp:
    def __init__(self):
        self.adc = ADC(Pin(8))   # create an ADC object acting on a pin
        self.adc.atten(ADC.ATTN_11DB)
        self.voltage_temp_map = [
                (1001, 100), (1000, 98), (999, 97), (998, 96), (997, 95), (996, 93),
                (995, 92), (994, 91), (993, 90), (992, 89), (991, 88), (990, 87),
                (989, 86), (988, 85), (987, 84), (986, 83), (985, 82), (984, 81),
                (982, 80), (981, 79), (980, 78), (978, 77), (977, 76), (975, 75),
                (974, 74), (972, 73), (971, 72), (969, 71), (967, 70), (965, 69),
                (963, 68), (961, 67), (959, 66), (957, 65), (955, 64), (953, 63),
                (950, 62), (948, 61), (943, 59), (940, 58), (937, 57), (934, 56),
                (931, 55), (928, 54), (924, 53), (921, 52), (917, 51), (914, 51),
                (910, 49), (906, 48), (902, 47), (898, 46), (893, 45), (889, 44),
                (884, 43), (879, 42), (874, 41), (869, 40), (864, 39), (858, 38),
                (852, 37), (846, 36), (840, 35), (834, 34), (827, 33), (821, 32),
                (814, 31), (806, 30), (799, 29), (791, 28), (784, 27), (776, 26),
                (767, 25), (759, 24), (750, 23), (741, 22), (732, 21), (713, 19),
                (703, 18), (692, 17), (682, 16), (671, 15), (661, 14), (650, 13),
                (638, 12), (627, 11), (615, 10), (604, 9), (592, 8), (579, 7),
                (567, 6), (555, 5), (542, 4), (530, 3), (517, 2), (504, 1),
                (0, 0)  # 最小值
            ]
    def value(self):
        mapped_value = self.adc.read()  # 读取 ADC 值（范围 0-4095）
        voltage= int((mapped_value / 4095) * 1023) 
        # 查找对应的温度
        for v, temp in self.voltage_temp_map:
            if voltage > v:
                return temp

        return 0  # 默认最低温度
# 土壤
class soilhumidity:
    def __init__(self):
        self.adc = ADC(Pin(8))   # create an ADC object acting on a pin
        self.adc.atten(ADC.ATTN_11DB)
    def value(self):
        raw_value = self.adc.read() 
        mapped_value = int((raw_value / 4095) * 1023) 
        return mapped_value
# 水位
class waterlevel:
    def __init__(self):
        self.adc = ADC(Pin(8))   # create an ADC object acting on a pin
        self.adc.atten(ADC.ATTN_11DB)

    def value(self):
        mapped_value = self.adc.read()  # 读取 ADC 值（范围 0-4095）
        voltage= int((mapped_value / 4095) * 1023) 
        water_level = self.map_voltage_to_level(voltage)
        return water_level

    def map_voltage_to_level(self, voltage):
        """将 ADC 读取值转换为水位百分比"""
        if voltage > 620:
            return 100
        elif voltage > 618:
            return 98
        elif voltage > 617:
            return 96
        elif voltage > 616:
            return 94
        elif voltage > 614:
            return 92
        elif voltage > 612:
            return 90
        elif voltage > 610:
            return 88
        elif voltage > 609:
            return 86
        elif voltage > 607:
            return 85
        elif voltage > 606:
            return 83
        elif voltage > 605:
            return 81
        elif voltage > 604:
            return 80
        elif voltage > 603:
            return 78
        elif voltage > 602:
            return 77
        elif voltage > 600:
            return 75
        elif voltage > 598:
            return 73
        elif voltage > 596:
            return 72
        elif voltage > 594:
            return 70
        elif voltage > 592:
            return 68
        elif voltage > 590:
            return 65
        elif voltage > 588:
            return 63
        elif voltage > 586:
            return 62
        elif voltage > 583:
            return 60
        elif voltage > 580:
            return 58
        elif voltage > 575:
            return 56
        elif voltage > 574:
            return 55
        elif voltage > 573:
            return 54
        elif voltage > 572:
            return 53
        elif voltage > 570:
            return 52
        elif voltage > 568:
            return 51
        elif voltage > 566:
            return 50
        elif voltage > 563:
            return 49
        elif voltage > 560:
            return 48
        elif voltage > 557:
            return 47
        elif voltage > 554:
            return 46
        elif voltage > 551:
            return 45
        elif voltage > 548:
            return 44
        elif voltage > 545:
            return 43
        elif voltage > 542:
            return 42
        elif voltage > 539:
            return 41
        elif voltage > 536:
            return 40
        elif voltage > 533:
            return 39
        elif voltage > 530:
            return 38
        elif voltage > 527:
            return 37
        elif voltage > 523:
            return 36
        elif voltage > 516:
            return 35
        elif voltage > 510:
            return 34
        elif voltage > 506:
            return 33
        elif voltage > 500:
            return 32
        elif voltage > 497:
            return 31
        elif voltage > 494:
            return 30
        elif voltage > 481:
            return 29
        elif voltage > 478:
            return 28
        elif voltage > 475:
            return 27
        elif voltage > 472:
            return 26
        elif voltage > 469:
            return 25
        elif voltage > 466:
            return 24
        elif voltage > 463:
            return 23
        elif voltage > 460:
            return 22
        elif voltage > 457:
            return 21
        elif voltage > 454:
            return 19
        elif voltage > 451:
            return 18
        elif voltage > 448:
            return 17
        elif voltage > 445:
            return 16
        elif voltage > 442:
            return 15
        elif voltage > 439:
            return 14
        elif voltage > 436:
            return 13
        elif voltage > 433:
            return 12
        elif voltage > 430:
            return 11
        elif voltage > 427:
            return 10
        elif voltage > 424:
            return 9
        elif voltage > 421:
            return 8
        elif voltage > 418:
            return 7
        elif voltage > 415:
            return 6
        elif voltage > 412:
            return 5
        elif voltage > 409:
            return 4
        elif voltage > 406:
            return 3
        elif voltage > 403:
            return 2
        elif voltage > 400:
            return 1
        else:
            return 0
# 人体红外
class pir:
    def __init__(self):
        self.pin = Pin(8, Pin.IN, Pin.PULL_UP)  # 初始化引脚8为输出模式

    def value(self):
        return 0 if self.pin.value() == 1 else 1