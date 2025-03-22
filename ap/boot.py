from machine import UART

uart = UART(2, 115200, rx=20, tx=19, bits=8, parity=None, stop=1)
uart_data = []
while True:
    while True:
        if uart.any():  # 判断接收缓冲区是否有数据
            data = uart.read(1)  # 读取1字节数据
            if data[0] == 0xAA:  # 如果包头正确
                uart_data.append(data[0])  # 将包头添加到数据列表
                break  # 跳出循环开始接收数据部分
    while len(uart_data) < 11:
        if uart.any():  # 判断接收缓冲区是否有数据
            data = uart.read(1)  # 读取1字节数据
            uart_data.append(data[0])
    if uart_data[-1] == 0xBB:
        print(uart_data)
        if uart_data[2] == 0:
            if uart_data[3] == 1:
                break
import os
import w25qxx
import esp_audio
import _thread
from machine import Pin, SPI
esp_audio.I2C_init()
esp_audio.audio_I2S_init()
esp_audio.audio_es8311_init()
spi = SPI(baudrate=10000000, polarity=1, phase=1, sck=Pin(1), mosi=Pin(2), miso=Pin(4))
cs = Pin(6, Pin.OUT)
flash = w25qxx.W25QXX_BlockDev(SPI = spi, CS_PIN = cs)
# with open("/music/starting_up.wav", 'rb') as f:
#     f.seek(1024)  # 跳过 WAV 文件头部，直接读取音频数据     
#     data = f.read()
      # 发送音频数据进行播放
uart.write(bytearray([0xff,0xff,0xff,0xff]))
# esp_audio.music_play(bytearray(data))
os.mount(flash, '/flash')