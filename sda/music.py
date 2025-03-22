import os
import w25qxx
import esp_audio
from machine import Pin, SPI,UART

spi = SPI(baudrate=10000000, polarity=1, phase=1, sck=Pin(1), mosi=Pin(2), miso=Pin(4))
cs = Pin(6, Pin.OUT)
flash = w25qxx.W25QXX_BlockDev(SPI = spi, CS_PIN = cs)
os.VfsFat.mkfs(flash)
os.mount(flash, '/flash')
