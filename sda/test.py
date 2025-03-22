# import icrobot
# import time
# import _thread
# import os
# from microdot import Microdot
# import network
# import gc
# from machine import Pin, SPI,UART
# 
# timeout = 10  # 设定10秒的超时时间
# last_pressed_time = None  # 记录按键按下的时间
# 
# def execute_file(filename):
#     global last_pressed_time
#     try:
#         with open(filename, 'r') as file:
#             code = file.read()
#         icrobot.start_execution()
#         time.sleep_ms(100)
#         exec(code, globals())
#     except Exception as e:
#         print(e)
#         last_pressed_time = None  # 记录按键按下的时间
#         icrobot.stop_execution()
#         icrobot.wifi.start_ap()
#         icrobot.file_start_flag = False
#         print(icrobot.file_flag)
#           
# def power_callback(pin):
#     time.sleep_ms(100)
#     if icrobot.power.value() == 0:
#         icrobot.file_start_flag = not icrobot.file_start_flag
#         print(icrobot.file_start_flag)
# 
# if __name__ == '__main__':
#     
#     my_scratch = icrobot.scratch()
#     # icrobot.expression.starting_up()
#     icrobot.power.irq(trigger=Pin.IRQ_FALLING, handler=power_callback)
#     # icrobot.expression.after_booting()
#     gc.enable()
#     icrobot.wifi.start_ap()
#     time.sleep_ms(100)
#     icrobot.camera.open()
#     time.sleep_ms(500)
#     # icrobot.ai.set_model(icrobot.ai.color_tracking)
#     # time.sleep_ms(500)
#     # icrobot.ai.set_color_tracking('red')
#     # while True:
#     #     print(icrobot.ai.color_istracked())
#     #     print(icrobot.ai.get_color_location('x'))
#     #     print(icrobot.ai.get_color_location('y'))
# #     icrobot.ai.set_model(icrobot.ai.qr_recognition)
# #     while True:
# #         print(icrobot.ai.qr_isrecognized())
# #         print(icrobot.ai.qr_result)
# #         time.sleep_ms(100)
# 
import time
import esp_audio
from machine import UART, Pin,reset
import _thread
import ubinascii
import icrobot

if __name__ == '__main__':
    icrobot.micphone.open()
    icrobot.asr.start()
    while True:
        if icrobot.asr.result() != -1
            print(icrobot.asr.result())
        time.sleep(0.2)
# import icrobot
# import time
# import _thread
# import os
# from microdot import Microdot
# import network
# import gc
# from machine import Pin, SPI,UART,ADC
# import module
# 
# if __name__ == '__main__':
#     
#     m1 = module.potentiometer()
#     while True:
#         val = m1.value()
#         print(val)
#         time.sleep(0.2)

from machine import UART, Pin, I2C
import time


data = [0x01,0x01,0x01,0x01,0x01]
data2 = [0x02,0x02,0x02,0x02,0x02]
def init_i2c():
    """重新初始化 I2C 总线"""
    global i2c  # 需要使用全局变量
    i2c = I2C(1, sda=Pin(7), scl=Pin(8), freq=100000)
    print("I2C 重新初始化完成")

init_i2c()
# 初始化按键引脚，内部上拉电阻
num = 0
while True:
    try:        
#         # 发送数据
#         i2c.writeto(0x0b, bytes(data))
#         print("发送数据:", data)
# 
#         # 读取 5 字节数据
#         num = i2c.readfrom(0x0b, 5)
#         print("收到数据:", list(num))
        # 发送数据
        i2c.writeto(0x06, bytes(data))
        i2c.writeto(0x0b, bytes(data))
        print("发送数据:", data)
        time.sleep(1)
        # 读取 5 字节数据
        i2c.writeto(0x06, bytes(data2))
        print("发送数据:", data2)
        time.sleep(1)
    except Exception as e:
        print("I2C 通信错误:", e)
        print("尝试重新初始化 I2C...")
        init_i2c()
        time.sleep(1)  # 等待 1 秒后重新尝试
    time.sleep(0.5)  # 控制发送频率



# from machine import UART, Pin, I2C
# import time
# 
# 
# data = [0x04,0x00,0x00,0x00]
# data[1] = 50
# data[2] = 0x01
# data[3] = 0x68
# 
# data1 = [0x04,0x00,0x00,0x00]
# data1[1] = 50
# data1[2] = 0xfe
# data1[3] = 0x98
# 
# i2c = I2C(1, sda=Pin(7), scl=Pin(8), freq=100000)
# # 初始化按键引脚，内部上拉电阻
# num = 0
# while True:
#     i2c.writeto(0x51, bytes(data))
#     time.sleep(1)
#     i2c.writeto(0x51, bytes(data1))
#     time.sleep(1)
#     num = num +2
#     print(num)


from machine import Pin, I2C
import time

time.sleep(5)
def init_i2c():
    """重新初始化 I2C 总线"""
    global i2c  # 需要使用全局变量
    i2c = I2C(1, sda=Pin(7), scl=Pin(8), freq=100000)
    print("I2C 重新初始化完成")
init_i2c()
power = Pin(5, Pin.IN, Pin.PULL_UP)
start = True
channel = 0

def select_channel(channel):
    while True:
        try: 
            """选择 PCA9548A 的一个通道（0-7）"""
            if channel < 0 or channel > 7:
                print("通道范围无效！")
                return
            # 写入控制字节，启用相应通道
            # 控制字节的每一位代表一个通道，0表示关闭，1表示启用
            control_byte = 1 << channel
            i2c.writeto(0x70, bytes([control_byte]))
            print(f"选择通道 {channel}")
            time.sleep(0.1)
            break
        except Exception as e:
            print("I2C 通信错误:", e)
            print("尝试重新初始化 I2C...")
            init_i2c()
            time.sleep(1) 
def zhao():
    try:        
        i2c.writeto(0x06, bytes([0x01,0x01,0x01,0x01,0x01]))
        time.sleep(1)
        # 读取 5 字节数据
        i2c.writeto(0x06, bytes([0x02,0x02,0x02,0x02,0x02]))
        time.sleep(1)
#         i2c.writeto(0x0b, bytes([0x01,0x01,0x01,0x01,0x01]))
#         time.sleep(1)
  
    except Exception as e:
        print("I2C 通信错误:", e)
        print("尝试重新初始化 I2C...")
        init_i2c()
        time.sleep(1)  # 等待 1 秒后重新尝试
def pao():
    try:        
        i2c.writeto(0x51, bytes([0x04,0x50,0x01,0x68]))
        time.sleep(0.8)
        i2c.writeto(0x51, bytes([0x04,0x50,0xfe,0x98]))
        time.sleep(0.8)
    except Exception as e:
        print("I2C 通信错误:", e)
        print("尝试重新初始化 I2C...")
        init_i2c()
        time.sleep(1)  # 等待 1 秒后重新尝试
def scan_i2c():
    """扫描 I2C 总线上的设备"""
    devices = i2c.scan()  # 扫描 I2C 总线上的设备
    if devices:
        for device in devices:
            print("发现设备: 0x{:02X}".format(device))  # 打印十六进制设备地址
    else:
        print("未发现 I2C 设备")
select_channel(0)
time.sleep(1)
while True:
    if power.value() == 0 :            
        start = not start
        print(start)
        while power.value() == 0:
            time.sleep(0.01)  # 等待按键释放
    if start:
        if channel == 0:
            zhao()
        elif channel == 1:
            select_channel(0)
            time.sleep(1)
            channel = 0
            zhao()
    if not start:
        if channel == 0:
            select_channel(1)
            time.sleep(1)
            channel = 1
            pao()
        elif channel == 1:
            pao()



import icrobot
import time
import _thread
import os
from microdot import Microdot
import network
import gc
from machine import Pin, SPI,UART
import module
import w25qxx
import esp_audio

def one_task():
    while True:
        print(1)
        time.sleep(1)
def two_task():
    a = 0
    while True:
        print(2)
        time.sleep(1)
        
if __name__ == '__main__':
    c = _thread.start_new_thread(one_task,(),2048)
    print("a:",c)
    b = _thread.start_new_thread(two_task,(),4096)
    print("b:",b)
    num = 1
    while True:
        print(3)
        num = num+1
        time.sleep(1)
        if num == 5:  
            _thread.delete(c)
    





            
            



