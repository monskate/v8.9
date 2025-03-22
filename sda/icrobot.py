from machine import UART,unique_id
import esp_audio
import esp_camera
import esp_who
from microdot import Microdot
import _thread
import network
import time
import gc
import ujson
import socket
import hashlib
import binascii

uart = UART(2, 115200, rx=20, tx=19, bits=8, parity=None, stop=1)
file_start_flag = False
file_flag = True
file_path = ['1.py','2.py','3.py','4.py','5.py','smartconfig.py']
file_num = 0

def send_command(command):
    """
    发送指令并等待应答
    如果 10ms 内没有收到正确的应答，则重新发送，最多重试 5 次
    """
    max_retries = 5  # 最大重试次数
    total_len = len(command) + 4
    buffer = bytearray(total_len)
    
    # 填充原始命令
    for i in range(len(command)):
        buffer[i] = command[i]
    
    # 计算并填充CRC
    crc_val = crc(buffer[:len(command)])
    buffer[len(command)] = crc_val & 0xFF
    buffer[len(command)+1] = (crc_val >> 8) & 0xFF
    
    # 填充尾部
    buffer[-2] = 0x66
    buffer[-1] = 0xbb

    for attempt in range(max_retries):
        uart.write(buffer)  # 发送指令
        start_time = time.ticks_ms()  # 记录起始时间
        while True:
            if uart_receive.reply == 1:  # 假设 1 表示成功应答
                uart_receive.reply = -1
                return True  # 发送成功，退出
            elif uart_receive.reply == 0:  # 收到无效应答，立即重发
                uart_receive.reply = -1
                break  # 退出 while 循环，立即重试
            # 超过 10ms 仍未收到应答，则超时
            if time.ticks_diff(time.ticks_ms(), start_time) > 10:
                break  # 退出 while 循环，重新发送

    return False  # 失败，返回 False

def crc(data: bytes) -> int:
    crc = 0xFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 0x0001:
                crc = (crc >> 1) ^ 0xA001
            else:
                crc >>= 1
    return crc

CORS_HEADERS = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type'
}

def video_stream_task(ip):
    app = Microdot()
    # 视频流
    @app.route('/video_feed', methods=['GET', 'OPTIONS'])
    def video_feed(request):
        def stream():
            yield b'--frame\r\n'
            while True:
                gc.collect()
                frame = esp_camera.capture()
                if frame is not None:
                    yield b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n--frame\r\n'
                else:
                    time.sleep_ms(10)
                    continue
        return stream(), 200, {
            'Content-Type': 'multipart/x-mixed-replace; boundary=frame',
            'Access-Control-Allow-Origin': '*'
        }

    # 启动视频流的Microdot应用
    app.run(host = ip,port=8081, debug=True) 

def video_start(ip):
    _thread.start_new_thread(video_stream_task, (ip,), 8* 1024)

class Power:
    def shuts_down(self):
        power = [0xaa, 0x55, 0x00,0xff,0x00]
        send_command(power)  
    def set_status(self,status):
        power = [0xaa, 0x55, 0x00,0x00,0x00]
        power[4] = status
        send_command(power)  
    def value(self):
        return uart_receive.power
power = Power()

class Camera:
    def __init__(self):
        self.camera_flag = False
    def open(self):
        """
        打开摄像头
        """
        gc.collect()
        time.sleep(0.1)
        if not self.camera_flag:
            cam = esp_camera.init(0, format=esp_camera.RGB565,framesize = esp_camera.FRAME_QVGA,xclk_freq = 16000000)
            if cam:
                print("Camera ready")
                self.camera_flag = True
            else:
                print("error")
                self.camera_flag = False
    def web_open(self):
        """
        打开摄像头
        """
        gc.collect()
        time.sleep(0.2)
        if not self.camera_flag:
            cam = esp_camera.init(0)
            if cam:
                print("Camera ready")
                self.camera_flag = True
            else:
                print("error")
                self.camera_flag = False
    def close(self):
        """
        关闭摄像头
        """
        if self.camera_flag:
            esp_camera.deinit()
            print("Camera close")
            time.sleep(0.5)
            gc.collect()
            self.camera_flag = False
    def set_pixel(self,num):
        if self.camera_flag:
            if num == 0:
                # esp_camera.framesize(esp_camera.FRAME_VGA)
                esp_camera.deinit()
                gc.collect()
                time.sleep(0.2)
                gc.collect()
                time.sleep(0.2)
                cam = esp_camera.init(0,framesize = esp_camera.FRAME_VGA)
            elif num == 1:
                # esp_camera.framesize(esp_camera.FRAME_SVGA) 
                esp_camera.deinit()
                gc.collect()
                time.sleep(0.2)
                gc.collect()
                time.sleep(0.2)
                cam = esp_camera.init(0,framesize = esp_camera.FRAME_SVGA)
            elif num == 2:
                # esp_camera.framesize(esp_camera.FRAME_XGA)
                esp_camera.deinit()
                gc.collect()
                time.sleep(0.2)
                gc.collect()
                time.sleep(0.2)
                cam = esp_camera.init(0,framesize = esp_camera.FRAME_XGA)
            elif num == 3:
                # esp_camera.framesize(esp_camera.FRAME_UXGA)  
                esp_camera.deinit()
                gc.collect()
                time.sleep(0.2)
                gc.collect()
                time.sleep(0.2)
                cam = esp_camera.init(0,framesize = esp_camera.FRAME_UXGA)
camera = Camera()

class Motor:
    def move_stop(self):
        """
        停止运动
        """
        move = [0xaa, 0x55, 0x01,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00]
        send_command(move)   
    def drive(self,left_speed,right_speed):
        """
        以（left_speed,right_speed）转动
        """
        move = [0xaa, 0x55, 0x01, 0x04,0x00,0x00,0x00,0x00,0x04,0x00,0x00,0x00,0x00]
        left_speed = max(-100, min(100, int(left_speed)))
        right_speed = max(-100, min(100, int(right_speed)))
        if left_speed < 0:
            move[4] = left_speed>>8
            move[5] = left_speed&0xff
        else:
            move[5] = left_speed
        if right_speed < 0:
            move[9] = right_speed>>8
            move[10] = right_speed&0xff
        else:
            move[10] = right_speed
        send_command(move)
    def leftmotor_drive(self,speed,duration=-1,distance=-1):
        """
        左轮以（）转动（）
        """
        global file_flag,file_start_flag
        move = [0xaa, 0x55, 0x01, 0x00,0x01,0x00,0x00,0x00,0x00]
        speed = max(-100, min(100, int(speed)))
        if speed < 0:
            move[5] = speed>>8
            move[6] = speed&0xff
        else:
            move[6] = speed
        if distance !=-1 and duration == -1:
            move[3] = 0x22
            move[7] = (distance >> 8) & 0xFF
            move[8] = distance & 0xFF
            send_command(move)
            uart_receive.lmotor_mode =2
            while True:
                if uart_receive.lmotor_mode == 0:
                    break
                if scratch.scratch_stop == True:
                    break
                if file_flag == True and file_start_flag == False:
                    break
                time.sleep_ms(10)
        elif duration !=-1 and distance == -1:
            move[3] = 0x21
            duration = duration * 10
            move[7] = (duration >> 8) & 0xFF
            move[8] = duration & 0xFF
            send_command(move) 
            uart_receive.lmotor_mode =1 
            while True:
                if uart_receive.lmotor_mode == 0:
                    break
                if scratch.scratch_stop == True:
                    break
                if file_flag == True and file_start_flag == False:
                    break
                time.sleep_ms(100)
        elif duration == -1 and distance == -1:
            move[3] = 0x23
            send_command(move) 
    def rightmotor_drive(self,speed,duration=-1,distance=-1):
        """
        右轮以（）转动（）
        """
        global file_flag,file_start_flag
        move = [0xaa, 0x55, 0x01, 0x00,0x02,0x00,0x00,0x00,0x00]
        speed = max(-100, min(100, int(speed)))
        if speed < 0:
            move[5] = speed>>8
            move[6] = speed&0xff
        else:
            move[6] = speed
        if distance !=-1 and duration == -1:
            move[3] = 0x22
            move[7] = (distance >> 8) & 0xFF
            move[8] = distance & 0xFF
            send_command(move) 
            uart_receive.rmotor_mode =2
            while True:
                if uart_receive.rmotor_mode == 0:
                    break
                if scratch.scratch_stop == True:
                    break
                if file_flag == True and file_start_flag == False:
                    break
                time.sleep_ms(100)
        elif duration !=-1 and distance == -1:
            move[3] = 0x21
            duration = duration * 10
            move[7] = (duration >> 8) & 0xFF
            move[8] = duration & 0xFF
            send_command(move) 
            uart_receive.rmotor_mode =1 
            while True:
                if uart_receive.rmotor_mode == 0:
                    break
                if scratch.scratch_stop == True:
                    break
                if file_flag == True and file_start_flag == False:
                    break
                time.sleep_ms(100)
        elif duration == -1 and distance == -1:
            move[3] = 0x23
            send_command(move) 
    def move_forward(self,speed,duration=-1,distance=-1):
        """
        机器人以(speed)速度前进(time)时间/秒
        机器人以(speed)速度前进(distance)距离/cm
        时间/距离均为None则一直前进
        """
        global file_flag,file_start_flag
        move = [0xaa, 0x55, 0x01, 0x00,0x02,0x00,0x00,0x00,0x00]
        speed = max(0, min(100, int(speed)))
        move[6] = speed
        if distance !=-1 and duration == -1:
            move[3] = 0x12
            move[7] = (distance >> 8) & 0xFF
            move[8] = distance & 0xFF
            send_command(move) 
            uart_receive.rmotor_mode = 2
            while True:
                if uart_receive.rmotor_mode == 0:
                    break
                if scratch.scratch_stop == True:
                    break
                if file_flag == True and file_start_flag == False:
                    break
        elif duration !=-1 and distance == -1:
            move[3] = 0x11
            duration = duration * 10
            move[7] = (duration >> 8) & 0xFF
            move[8] = duration & 0xFF
            send_command(move) 
            uart_receive.rmotor_mode = 1
            while True:
                if uart_receive.rmotor_mode == 0:
                    break
                if scratch.scratch_stop == True:
                    break
                if file_flag == True and file_start_flag == False:
                    break
        elif duration == -1 and distance == -1:
            move[3] = 0x13
            send_command(move) 
    def move_backward(self,speed,duration=-1,distance=-1):
        """
        机器人以(speed)速度后退(time)时间/秒
        机器人以(speed)速度后退(distance)距离/cm
        时间/距离均为None则一直后退
        """
        global file_flag,file_start_flag
        move = [0xaa, 0x55, 0x01, 0x00,0x04,0x00,0x00,0x00,0x00]
        speed = max(0, min(100, int(speed)))
        move[6] = speed
        if distance !=-1 and duration == -1:
            move[3] = 0x12
            move[7] = (distance >> 8) & 0xFF
            move[8] = distance & 0xFF
            send_command(move)
            uart_receive.rmotor_mode = 2 
            while True:
                if uart_receive.rmotor_mode == 0:
                    break
                if scratch.scratch_stop == True:
                    break
                if file_flag == True and file_start_flag == False:
                    break
        elif duration !=-1 and distance == -1:
            move[3] = 0x11
            duration = duration * 10
            move[7] = (duration >> 8) & 0xFF
            move[8] = duration & 0xFF
            send_command(move) 
            uart_receive.rmotor_mode = 1
            while True:
                if uart_receive.rmotor_mode == 0:
                    break
                if scratch.scratch_stop == True:
                    break
                if file_flag == True and file_start_flag == False:
                    break      
        elif duration == -1 and distance == -1:
            move[3] = 0x13
            send_command(move) 
    def turn_left(self,speed,duration=-1,distance=-1):
        """
        机器人以(speed)速度左转(time)时间/秒
        机器人以(speed)速度左转(distance)距离/cm
        时间/距离均为None则一直左转
        """
        global file_flag,file_start_flag
        move = [0xaa, 0x55, 0x01, 0x00,0x06,0x00,0x00,0x00,0x00]
        speed = max(0, min(100, int(speed)))
        move[6] = speed
        if distance !=-1 and duration == -1:
            move[3] = 0x12
            move[7] = (distance >> 8) & 0xFF
            move[8] = distance & 0xFF
            send_command(move)  
            uart_receive.rmotor_mode = 2
            while True:
                if uart_receive.rmotor_mode == 0:
                    break
                if scratch.scratch_stop == True:
                    break
                if file_flag == True and file_start_flag == False:
                    break
        elif duration !=-1 and distance == -1:
            move[3] = 0x11
            duration = duration * 10
            move[7] = (duration >> 8) & 0xFF
            move[8] = duration & 0xFF
            send_command(move)
            uart_receive.rmotor_mode = 1  
            while True:
                if uart_receive.rmotor_mode == 0:
                    break
                if scratch.scratch_stop == True:
                    break
                if file_flag == True and file_start_flag == False:
                    break       
        elif duration == -1 and distance == -1:
            move[3] = 0x13
            send_command(move)  
    def turn_right(self,speed,duration=-1,distance=-1):
        """
        机器人以(speed)速度右转(time)时间/秒
        机器人以(speed)速度右转(distance)距离/cm
        时间/距离均为None则一直右转
        """
        global file_flag,file_start_flag
        move = [0xaa, 0x55, 0x01, 0x00,0x08,0x00,0x00,0x00,0x00]
        speed = max(0, min(100, int(speed)))
        move[6] = speed
        if distance !=-1 and duration == -1:
            move[3] = 0x12
            move[7] = (distance >> 8) & 0xFF
            move[8] = distance & 0xFF
            send_command(move)  
            uart_receive.rmotor_mode = 2
            while True:
                if uart_receive.rmotor_mode == 0:
                    break
                if scratch.scratch_stop == True:
                    break
                if file_flag == True and file_start_flag == False:
                    break
        elif duration !=-1 and distance == -1:
            move[3] = 0x11
            duration = duration * 10
            move[7] = (duration >> 8) & 0xFF
            move[8] = duration & 0xFF
            send_command(move)  
            uart_receive.rmotor_mode = 1
            while True:
                if uart_receive.rmotor_mode == 0:
                    break
                if scratch.scratch_stop == True:
                    break
                if file_flag == True and file_start_flag == False:
                    break     
        elif duration == -1 and distance == -1:
            move[3] = 0x13
            send_command(move)  
    def left_speed(self):
        return uart_receive.lmotor_speed
    def left_moving_distance(self):
        return uart_receive.lmotor_distance
    def right_speed(self):
        return uart_receive.rmotor_speed
    def right_moving_distance(self):
        return uart_receive.rmotor_distance
motor = Motor()
         
class Gripper:
    def open(self,port):
        """
        端口(port)机械手松开
        """
        paw = [0xaa, 0x55, 0x04, 0x00,0x02]
        paw[3] = port
        send_command(paw) 
        
    def close(self,port):
        """
        端口(port)机械手抓取
        """
        paw = [0xaa, 0x55, 0x04, 0x00,0x01]
        paw[3] = port
        send_command(paw) 
    
    def open_until_done(self,port):
        """
        端口(port)机械手动作直到完成
        """
        paw = [0xaa, 0x55, 0x04, 0x00,0x02]
        paw[3] = port
        send_command(paw) 
        uart_receive.gripper = 1
        while True:
            if uart_receive.gripper == 0 and uart_receive.gripper_port ==port:
                break
            if scratch.scratch_stop == True:
                break
            time.sleep_ms(10)

    def close_until_done(self,port):
        """
        端口(port)机械手抓取直到完成
        """
        paw = [0xaa, 0x55, 0x04, 0x00,0x01]
        paw[3] = port
        send_command(paw) 
        uart_receive.gripper = 1
        while True:
            if uart_receive.gripper == 0 and uart_receive.gripper_port ==port:
                break
            if scratch.scratch_stop == True:
                break
            time.sleep_ms(100)
gripper = Gripper()

class Gun:
    def fire(self,port,num):
        """
        端口(port)炮台发射(num)颗弹珠
        """
        fire = [0xaa, 0x55, 0x05, 0x00,0x01,0x00]
        fire[3] = port
        fire[5] = num
        send_command(fire) 

    def fire_until_done(self,port,num):
        """
        端口(port)炮台发射是否完成
        """
        fire = [0xaa, 0x55, 0x05, 0x00,0x01,0x00]
        fire[3] = port
        fire[5] = num
        send_command(fire) 
        uart_receive.gun = 1
        while True:
            if uart_receive.gun == 0 and uart_receive.gun_port ==port:
                break
            if scratch.scratch_stop == True:
                break
            time.sleep_ms(100)
gun = Gun()
 
class Display:
    def __init__(self):
        self.brightness = 1
    def set_brightness(self,lum):
        """
        亮度设置为[]
        """
        oled = [0xaa, 0x55, 0x03, 0x01,0x00]
        oled[4]=lum
        send_command(oled)       
    def show_image(self,image,mode):
        """
        点阵显示自定义数据
        """
        oled = [0xaa, 0x55, 0x03, 0x02,0x00]
        oled = oled + image
        oled[4] = mode
        send_command(oled)    
    def show_text(self,var,mode):
        """
        点阵显示字符串
        """
        var_bytes = var.encode('utf-8')
        oled = [0xaa, 0x55, 0x03,0x03,0x00,0x00]
        oled[4] = mode
        oled[5] = len(var_bytes)
        oled += list(var_bytes) 
        send_command(oled) 
    def show_expression(self,num):
        oled = [0xaa, 0x55, 0x03,0x04,0x00]
        oled[4] = num
        send_command(oled) 
    def set_pixel(self,pos_x,pos_y):
        """
        点阵点亮指定点(只)
        """
        oled = [0xaa, 0x55, 0x03, 0x02,0x00]
        if not (0 <= pos_x < 24 and 0 <= pos_y < 8):
            return 
        image = [0x00] * 24
        image[pos_x] |= (1 << pos_y)
        oled = oled + image
        send_command(oled) 
    def add_pixel(self,pos_x,pos_y):
        """
        点阵点亮指定点(增加)
        """
        oled = [0xaa, 0x55, 0x03, 0x05]
        if not (0 <= pos_x < 24 and 0 <= pos_y < 8):
            return 
        image = [1,pos_x,pos_y]
        oled = oled + image
        send_command(oled) 
    def clear_pixel(self,pos_x,pos_y):
        """
        点阵点亮指定点(删除)
        """
        oled = [0xaa, 0x55, 0x03, 0x05]
        if not (0 <= pos_x < 24 and 0 <= pos_y < 8):
            return 
        image = [0,pos_x,pos_y]
        oled = oled + image
        send_command(oled) 
    def toggle_pixel(self,pos_x,pos_y):
        """
        点阵翻转指定点
        """
        oled = [0xaa, 0x55, 0x03, 0x05]
        if not (0 <= pos_x < 24 and 0 <= pos_y < 8):
            return 
        image = [2,pos_x,pos_y]
        oled = oled + image
        send_command(oled) 
    def clear(self):
        """
        熄屏
        """
        oled = [0xaa, 0x55, 0x03, 0x02,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00]
        send_command(oled) 
display = Display()        

class Speaker:
    def __init__(self):
        self.music_flag = False
        self.music_start = False
        self.vol = 7
    def music_play_thread(self,filename):
        self.music_start = True
        self.music_flag = True
        with open(filename, 'rb') as f:
            f.seek(1024)  # 跳过 WAV 文件头部，直接读取音频数据     
            while self.music_flag:
                data = f.read(1024)
                if not data:  # 文件结束时退出
                    break
                esp_audio.music_play(bytearray(data))  # 发送音频数据进行播放
            self.music_flag = False
            self.music_start = False
    def play_music(self,filename):
        """
        播放音乐(非阻塞)
        """
        if self.music_flag:
            self.music_flag = False
        while self.music_start:
            pass
        _thread.start_new_thread(self.music_play_thread, (filename,),5*1024)   
    def stop_sounds(self):
        """
        停止所有声音
        """
        self.music_flag = False       
    def set_volume(self,vol):
        """
        设置喇叭音量
        """
        vol = max(0, min(10, int(vol)))
        self.vol = vol
        if vol == 0:
            esp_audio.music_vol_set(vol)
        else:
            esp_audio.music_vol_set(37+(vol-1)*7)
    def play_music_until_done(self,filename):
        """
        播放音乐(阻塞)
        """
        self.music_flag = True
        with open(filename, 'rb') as f:
            f.seek(1024)  # 跳过 WAV 文件头部，直接读取音频数据     
            while self.music_flag:
                data = f.read(1024)
                if not data:  # 文件结束时退出
                    break
                esp_audio.music_play(bytearray(data))  # 发送音频数据进行播放
            self.music_flag = False
speaker = Speaker()

class Rgb_sensor: 
    def __init__(self):
        self.line_flag = False
    def start_grayscale_learning(self):
        """
        开始灰度学习
        """
        color = [0xaa, 0x55, 0x02, 0x04]
        send_command(color) 
    def start_color_learning(self,num):
        """
        开始颜色学习
        :num:  1-7:红到紫
        """
        color = [0xaa, 0x55, 0x02, 0x05,0x00]
        color[4] = num
        send_command(color) 
    def set_line_mode(self,mode):
        """
        设置巡线传感器模式
        :mode: 1 :二值  2:灰度 3:颜色
        """
        color = [0xaa, 0x55, 0x02, 0x00]
        color[3] = mode
        send_command(color) 
    def close(self):
        """
        关闭巡线传感器
        """
        color = [0xaa, 0x55, 0x02, 0x00]
        send_command(color)
    def read_line_value(self,num):
        """
        读取探头（num）的值
        """
        time.sleep_ms(5)
        if num == 5:
            data = uart_receive.line
        else:
            data = uart_receive.line[num]
        return data
    def line_tracking_thread(self,speed):
        """
        自动巡线
        """
        BaseSpeed = speed
        if 0 < speed < 45:
            Kp = 0.13
            Kd = 0.07
        elif 45 <= speed < 55:
            Kp = 0.14
            Kd = 0.12
        elif 55 <= speed <= 60:
            Kp = 0.17
            Kd = 0.23
        dall = 0
        RSpeed = 0
        LSpeed = 0
        lasterror = 0
        Motor = 0
        error = 0
        while self.line_flag:
            line = uart_receive.line
            if line:
                error = line[4]*1.5+line[3]-line[1]-line[0]*1.5
                dall = error-lasterror
                Motor = Kp*error + dall*Kd
                LSpeed = BaseSpeed - Motor
                RSpeed = BaseSpeed + Motor
                lasterror = error
                motor.drive(LSpeed, RSpeed)
        motor.drive(0, 0)
        rgb_sensor.close()
    def line_tracking_until(self,speed,line_data):
        """
        自动巡线直到
        """
        BaseSpeed = speed
        if 0 < speed < 45:
            Kp = 0.13
            Kd = 0.07
        elif 45 <= speed < 55:
            Kp = 0.14
            Kd = 0.12
        elif 55 <= speed <= 60:
            Kp = 0.17
            Kd = 0.23
        dall = 0
        RSpeed = 0
        LSpeed = 0
        lasterror = 0
        Motor = 0
        error = 0
        rgb_sensor.set_line_mode(2)
        while self.line_flag:
            line = uart_receive.line
            if line:
                bin_line = [1 if value <= 100 else 0 for value in line]
                print(bin_line)
                if bin_line == line_data:
                    motor.drive(0, 0)
                    rgb_sensor.close()
                    break
                else:
                    error = line[4]*1.5+line[3]-line[1]-line[0]*1.5
                    dall = error-lasterror
                    Motor = Kp*error + dall*Kd
                    LSpeed = BaseSpeed - Motor
                    RSpeed = BaseSpeed + Motor
                    lasterror = error
                    motor.drive(LSpeed, RSpeed) 
    def line_tracking(self,speed):
        if not self.line_flag:
            self.line_flag = True
            rgb_sensor.set_line_mode(2)
            _thread.start_new_thread(rgb_sensor.line_tracking_thread, (speed,))
    def stop_line_tracking(self):
        self.line_flag = False
rgb_sensor = Rgb_sensor()    

class Leftkey:
    def value(self):
        return uart_receive.lkey
leftkey = Leftkey()

class Rightkey:
    def value(self):
        return uart_receive.rkey
rightkey = Rightkey()

class Privacy_switch:
    def value(self):
        return uart_receive.privacy_switch
privacy_switch = Privacy_switch()

class AI:
    def __init__(self):
        self.ai_start = False
        self.ai_set = False
        self.color_x = 0
        self.color_y = 0
        self.qr_result = ''
        self.face_result = [0,0,0,0,0]
        self.color = [0,0]

    def color_tracking(self):
        esp_who.ai_color_init()
        while not self.ai_set:
            pass
        while self.ai_start:
            if not self.ai_set:
                continue
            result = esp_who.ai_color()
            if result is None or len(result) < 2:
                print("No result")
                continue
            if result[0] is not None:
                self.color = result
                self.color_x = result[0]
                self.color_y = result[1]
            time.sleep_ms(100)
        esp_who.ai_color_deinit()
                
    def qr_recognition(self):
        esp_who.ai_qr_init()
        while self.ai_start:   
            result = esp_who.ai_qr()
            if result is not None:
                self.qr_result = result
            else:
                self.qr_result = ''
            time.sleep_ms(100)
        esp_who.ai_qr_deinit()
        
    def face_detection(self):
        print(1)
        esp_who.ai_face_detection_init()
        print(2)
        while self.ai_start:
            print(3)
            result = esp_who.ai_face_detection()
            print(4)
            if result is None or len(result) < 5:
                print("No result")
                continue
            print(result)
            self.face_result = result
            # time.sleep_ms(100)
        esp_who.ai_face_detection_deinit()           

    def set_model(self,model):
        """
        设置为（）识别模式
        """
        if self.ai_start:
            self.ai_start = False
            time.sleep(0.5)
        self.ai_start = True
        _thread.start_new_thread(model,())

    def close_model(self):
        """
        设置为（）识别模式
        """
        self.ai_start = False

    def set_color_tracking(self,color):
        """
        设置为追踪（）颜色
        """
        time.sleep(1)
        self.ai_set = False
        print(color)
        esp_who.ai_color_set(color)
        self.ai_set = True

    def color_istracked(self):
        """
        是否追踪到颜色
        """
        if self.color_x == 0 and self.color_y == 0:
            return False
        else:
            return True
        
    def get_color_location(self,mode):
        """
        色块位置
        """
        if mode == "x":    
            return self.color_x
        if mode == "y":    
            return self.color_y
    
    def qr_isrecognized(self):
        """
        是否识别到二维码
        """
        if self.qr_result == '':
            return False
        else:
            return True
        
    def get_qr_information(self):
        """
        二维码信息
        """
        if self.qr_result != '':
            return self.qr_result
            
    def face_isdetected(self):
        """
        是否检测到人脸
        """
        if self.face_result[0] > 0:
            return True
        else:
            return False
        
    def get_face_number(self):
        """
        人脸数量
        """
        return self.face_result[0]
       
    def get_face_location(self,mode):
        """
        人脸位置
        """
        if mode == "x":  
            if self.face_result[0] > 0:  
                return int((self.face_result[1]+self.face_result[2])/2)
            else:
                return 0
        if mode == "y":  
            if self.face_result[0] > 0:    
                return int((self.face_result[3]+self.face_result[4])/2)
            else:
                return 0
ai = AI() 

class ASR:
    def __init__(self):
        self.data = -1
        self.asr_start = False

    def audio_thread(self):
        last_result = -1
        while self.asr_start:
            result = esp_audio.ai_audio_result()
            if result != last_result:
                self.data = result
                last_result = result
            time.sleep_ms(100)
        esp_audio.ai_audio_deinit()

    def start(self):
        if not self.asr_start:
            esp_audio.ai_audio_start()
            self.asr_start = True
            _thread.start_new_thread(self.audio_thread, ())

    def stop(self):
        self.asr_start = False
    def result(self):
        return self.data

    def vol(self):
        if not self.asr_start:
            vol=esp_audio.ai_audio_vol()
            return vol       
asr = ASR()

def start_execution():
    """开始执行程序"""
    power.set_status(0)

def stop_execution():
    """停止执行程序"""
    global file_flag,file_num
    if file_flag:
        print("file停止")
        file_num = 0
        speaker.music_flag = False
        rgb_sensor.line_flag = False
        ai.ai_start = False
        power.set_status(255)
        camera.close()
        gc.collect()
    if not file_flag:
        print("scratch停止")
        speaker.music_flag = False
        rgb_sensor.line_flag = False
        camera.close()
        time.sleep_ms(1)
        power.set_status(254)
        gc.collect()

class WiFi:
    def __init__(self):
        self.sta = network.WLAN(network.STA_IF)
        self.ap = network.WLAN(network.AP_IF)
        # 生成唯一默认AP名称
        chip_id = binascii.hexlify(unique_id()).decode('utf-8')
        self.default_ap_ssid = f"ICRobot-{chip_id[-4:]}"
        self.channel = 6
        self.ap_config = '/ap.config'
        self.sta_config = '/sta.config'
        self.sta_isconnected = False
        self.sta_connecting = False
        self.ssid = ''
        self.password = ''
        self.ap_state = False
        self.ap_flag = False

    def load_ap(self):
        """从文件加载保存的ap模式SSID"""
        try:
            with open(self.ap_config, "r") as f:
                config = ujson.load(f)
                print(config.get('ssid'))
                return config.get('ssid')
        except:
            return None

    def save_ap(self, ssid):
        """保存ap模式到SSID到文件"""
        try:
            with open(self.ap_config, "w") as f:
                ujson.dump({"ssid": ssid}, f)
            return True
        except Exception as e:
            print("保存SSID失败:", e)
            return False

    def ap_task(self,ssid):
        global file_flag
        if self.ap.active():
            return
        else:
            self.ap_flag = True
            self._disable_sta()
            if ssid is None:
                ssid = self.load_ap() or self.default_ap_ssid
            print('- AP mode :', ssid)
            self.ap.active(True)
            self.ap.config(essid=ssid,channel = self.channel,max_clients=1)
            
            start = time.ticks_ms()
            while not self.ap.active():
                if time.ticks_diff(time.ticks_ms(), start) > 5000:
                    raise RuntimeError("AP启动失败")
                time.sleep(0.1)
            print('- AP mode enabled:', self.ap.ifconfig()) 
            connected_stations = set()
            while self.ap_flag :
                current_stations = set(self.ap.status('stations'))
    #             # 检查是否有新的客户端连接
                new_connections = current_stations - connected_stations
                if new_connections:
                    print("连接")
                    self.ap_state = True
                    self.ap.set_hide_ssid(int(1))
                    connected_stations.update(new_connections)
    # 
    #             # 检查是否有客户端断开连接
                disconnected_stations = connected_stations - current_stations
                if disconnected_stations:
                    print("断开")
                    self.ap_state = False
                    if not file_flag:
                        file_flag = True
                        stop_execution()
                    connected_stations.difference_update(disconnected_stations)
                    self.ap.set_hide_ssid(int(0))
                time.sleep(1)  
    
    def start_ap(self,ssid=None):
        """启动AP模式"""
        _thread.start_new_thread(self.ap_task,(ssid,))

    def stop_ap(self):
        """关闭AP模式"""
        self.ap_flag = False
        self.ap.active(False)
        while self.ap.active():
            time.sleep(0.1)
        print("AP模式已关闭")

    def change_channel(self,channel):
        """改变通道"""
        self.channel = channel
        self.stop_ap()
        self.start_ap()

    def connect_sta(self,ssid,password):
        """连接STA网络"""
        self._disable_ap()
        self._disable_sta()
    
        if not self.sta.active():
            self.sta.active(True)
    
        print(f"尝试连接: {ssid}")
        self.sta.connect(ssid, password)

    def is_connected(self):
        return self.sta.isconnected()

    def information(self):
        return self.sta.ifconfig()

    def disconnect_sta(self):
        """断开STA连接"""
        self.sta.disconnect()
        self.sta.active(False)
        while self.sta.isconnected():
            time.sleep(0.1)
        print("STA已断开")
        return True
    
    def start_ap_with_web(self):
        self.start_ap()
        _thread.start_new_thread(self.start_webserver, ())
        while True:
            if self.sta_connecting:
                time.sleep(1)
                self._disable_ap()
                if not self.sta.active():
                    self.sta.active(True)
                    self.connect_sta(self.ssid, self.password)
                    # 等待连接
                    start = time.ticks_ms()
                    while not self.is_connected():
                        if time.ticks_diff(time.ticks_ms(), start) > 10000:  # 等待最多10秒
                            print(f"连接Wi-Fi {self.ssid} 超时")
                            break
                        time.sleep(0.1)

                    if self.is_connected():
                        print(f"成功连接到Wi-Fi: {self.ssid}")
                        return  # 成功连接后，直接返回
                    else:
                        print(f"无法连接到Wi-Fi: {self.ssid}")   
                        print("请重新配网！")  
                        self.start_ap()
                        self.sta_connecting = False

    def _disable_ap(self):
        if self.ap.active():
            self.ap.active(False)
            while self.ap.active():
                time.sleep(0.1)

    def _disable_sta(self):
        if self.sta.active():
            self.sta.disconnect()
            self.sta.active(False)
            while self.sta.isconnected():
                time.sleep(0.1)
            while self.sta.active():
                time.sleep(0.1)

    def scan_and_connect_wifi(self):
        """扫描二维码并连接WiFi，连接失败或超时则退出"""
        camera.open()
        ai.set_model(ai.qr_recognition)
        
        speaker.play_music_until_done("/music/distribution_network.wav")
        start_scan_time = time.ticks_ms()  # 记录扫描开始时间
        
        while True:
            if time.ticks_diff(time.ticks_ms(), start_scan_time) > 10000:  # 超过10秒
                print("10秒内未扫描到 WiFi 二维码，退出扫描。")
                ai.close_model()
                camera.close()
                return False  # 退出扫描
            
            if ai.qr_isrecognized and ai.get_qr_information():
                qr_data = ai.get_qr_information()

                if qr_data.startswith("WIFI:"):
                    speaker.play_music("/music/saomadi.wav")
                    try:
                        wifi_info = qr_data[5:-2]  # 去掉 "WIFI:" 和 结尾的 ";;"
                        wifi_dict = dict(item.split(":") for item in wifi_info.split(";") if ":" in item)

                        ssid = wifi_dict.get("S", "")
                        password = wifi_dict.get("P", "")
                        if ssid:
                            if not self.sta.active():
                                self.sta.active(True)
                            self.sta.connect(ssid, password)
                            print(f"尝试连接: {ssid}, {password}")
                            
                            start_time = time.ticks_ms()  # 记录WiFi连接开始时间
                            while not self.sta.isconnected():
                                if time.ticks_diff(time.ticks_ms(), start_time) > 5000:  # 连接超时
                                    print("WiFi 连接超时，重新扫描二维码...")
                                    break  # 重新扫描

                            if self.sta.isconnected():  # 连接成功才播放提示音
                                print("WiFi 连接成功！")
                                ai.close_model()
                                camera.close()
                                speaker.play_music("/music/connection_successful.wav")
                                return True  # 连接成功，退出函数

                    except Exception as e:
                        print("error:", e)

wifi = WiFi()

class MyWebsocket:
    def __init__(self):
        # WebSocket 操作码常量
        self.TEXT = 1
        self.BINARY = 2
        self.CLOSE = 8

    def handshake(self, client_socket):
        """执行 WebSocket 握手"""
        # 接收客户端的握手请求
        request = client_socket.recv(1024).decode('utf-8')
        headers = self.parse_headers(request)

        # 从请求头中获取 Sec-WebSocket-Key
        websocket_key = headers.get('Sec-WebSocket-Key')

        if not websocket_key:
            print("WebSocket Key not found!")
            client_socket.close()
            return

        # 计算 Sec-WebSocket-Accept
        accept_value = self.generate_accept_value(websocket_key)

        # 发送 WebSocket 握手响应
        response = (
            "HTTP/1.1 101 Switching Protocols\r\n"
            "Upgrade: websocket\r\n"
            "Connection: Upgrade\r\n"
            f"Sec-WebSocket-Accept: {accept_value}\r\n\r\n"
        )
        client_socket.send(response.encode('utf-8'))

    def parse_headers(self, request):
        """解析 WebSocket 请求头"""
        headers = {}
        for line in request.split("\r\n")[1:]:
            if not line:
                continue
            header, value = line.split(":", 1)
            headers[header.strip()] = value.strip()
        return headers

    def generate_accept_value(self, websocket_key):
        """生成 WebSocket 握手响应的 Sec-WebSocket-Accept 值"""
        websocket_guid = '258EAFA5-E914-47DA-95CA-C5AB0DC85B11'
        sha1_hash = hashlib.sha1((websocket_key + websocket_guid).encode('utf-8')).digest()
        return binascii.b2a_base64(sha1_hash).decode('utf-8').strip()

    def receive(self, client_socket):
        """接收 WebSocket 消息"""
        
        header = client_socket.recv(2)
        if len(header) < 2:
            return None  # Connection closed

        # 解析帧头
        fin, opcode, has_mask, length = self.parse_frame_header(header)

        if length == 126:
            length = int.from_bytes(client_socket.recv(2), 'big')
        elif length == 127:
            length = int.from_bytes(client_socket.recv(8), 'big')

        # 读取掩码
        if has_mask:
            mask = client_socket.recv(4)
            if len(mask) < 4:
                return None

        # 读取数据
        payload = client_socket.recv(length)
        if len(payload) < length:
            return None

        # 如果有掩码，解掩码
        if has_mask:
            payload = bytes(b ^ mask[i % 4] for i, b in enumerate(payload))

        # 处理 WebSocket 操作码
        if opcode == self.TEXT:
            try:
                return payload.decode('utf-8')
            except UnicodeError:
                print("Warning: Received invalid UTF-8 data, returning raw bytes.")
                return payload 
        elif opcode == self.BINARY:
            return payload
        # elif opcode == self.CLOSE:
        #     close_frame = bytearray([0x88, 0x00])  # FIN + Close, 长度0
        #     client_socket.send(close_frame)
        #     print("Client closed the connection.")
        #     return None
        return None

    def parse_frame_header(self, header):
        """解析 WebSocket 数据帧头"""
        fin = header[0] & 0x80
        opcode = header[0] & 0x0F
        has_mask = header[1] & 0x80
        length = header[1] & 0x7F

        return fin, opcode, has_mask, length

    def send(self, client_socket, message):
        """发送 WebSocket 消息"""
        # 确定消息的长度
        if isinstance(message, str):
            message = message.encode('utf-8')
            opcode = self.TEXT
        else:
            opcode = self.BINARY

        length = len(message)

        frame = bytearray()
        frame.append(0x80 | opcode)

        if length < 126:
            frame.append(length)
        elif length < (1 << 16):
            frame.append(126)
            frame.extend(length.to_bytes(2, 'big'))
        else:
            frame.append(127)
            frame.extend(length.to_bytes(8, 'big'))

        frame.extend(message)

        # 发送消息帧
        client_socket.send(frame)

class Scratch:
    def __init__(self):
        self.speak_port = 8080
        self.send_port = 8082
        self.receive_port = 8083
        self.mode_port = 8084
        self.scratch_stop = False
        self.speaker_flag = False
        self.cmd_handlers = {
            "camera": self.handle_camera,
            "micphone": self.handle_micphone,
            "motor": self.handle_motor,
            "gripper": self.handle_gripper,
            "gun": self.handle_gun,
            "display": self.handle_display,
            "speaker": self.handle_speaker,
            "rgb_sensor": self.handle_rgb_sensor,
            "line_tracking": self.handle_line_tracking,
            "upload_script": self.handle_upload_script,
            "update_ap": self.update_ap
        }
        self.websocket = MyWebsocket()

    def start_send(self,host):
        """启动 WebSocket 发送服务器"""
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind((host, self.send_port))
        server_socket.listen(1)  # 最大连接数为 1，只允许一个客户端连接
        print(f"WebSocket Server Send started on {host}:{self.send_port}")
        while True:
            client_socket, client_address = server_socket.accept()
            print(f"Send Connection from {client_address}")
            self.handle_client_send(client_socket)
            time.sleep(0.5)

    def handle_client_send(self, client_socket):
        """处理 WebSocket 客户端连接"""
        global file_flag
        # 握手过程
        self.websocket.handshake(client_socket)
        while True:
            try:
                if file_flag:
                    break 
                keys = [uart_receive.lkey,uart_receive.rkey,uart_receive.privacy_switch]
                vol = [asr.vol()]
                num = [uart_receive.power,uart_receive.lmotor_speed,uart_receive.rmotor_speed,uart_receive.lmotor_distance,uart_receive.rmotor_distance]
                data = uart_receive.line
                device_status = keys+vol+ num + data
                # 发送设备状态
                device_status_json = ujson.dumps(device_status)
                self.websocket.send(client_socket, device_status_json) 
                time.sleep_ms(1)
            except Exception as e:
                print(f"send Error: {e}")
                break
        gc.collect()
        # 关闭连接后清理资源
        client_socket.close()
        print("Connection closed. Ready for a new client.")
             
    def start_receive(self,host):
        """启动 WebSocket 接收服务器"""
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind((host, self.receive_port))
        server_socket.listen(1)  # 最大连接数为 1，只允许一个客户端连接
        print(f"WebSocket Server Receive started on {host}:{self.receive_port}")

        while True:
            client_socket, client_address = server_socket.accept()
            print(f"Receive Connection from {client_address}")
            self.handle_client_receive(client_socket)
            time.sleep(0.5)

    def handle_client_receive(self, client_socket):
        """处理 WebSocket 客户端连接"""
        global file_flag
        self.scratch_stop = False
        # 握手过程
        self.websocket.handshake(client_socket)
        client_socket.setblocking(False)
        last_recv_time = time.ticks_ms()
        while True:
            try:
                if file_flag:
                    break
                if self.scratch_stop == True:
                    break
                if time.ticks_diff(time.ticks_ms(), last_recv_time) > 20000:
                    print("Timeout: No data received for 20 seconds. Closing connection.")
                    break
                message = self.websocket.receive(client_socket)
                if message:
                    last_recv_time = time.ticks_ms() 
                    if message =='1':
                        continue
                    print(message)
                    self.process_message(client_socket, message)
                    self.websocket.send(client_socket,'success')
                    print("执行完毕")
                else:
                    print("Client disconnected.")
                    break
                time.sleep_ms(1)
            except OSError as e:
                # MicroPython 中非阻塞模式无数据时的错误码通常是 11 (EAGAIN)
                if e.args[0] == 11:  # 11 是 EAGAIN/EWOULDBLOCK 的常见错误码
                    continue
                else:
                    print(f"Socket 错误: {e}")
                    break
            except Exception as e:
                print(f"Unexpected error: {e}")
                break
        gc.collect()
        stop_execution()
        # 关闭连接后清理资源
        client_socket.close()
        print("send closed. Ready for a new client.")

    def start_mode(self,host):
        """启动 WebSocket 设置服务器"""
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind((host, self.mode_port))
        server_socket.listen(1)  # 最大连接数为 1，只允许一个客户端连接
        print(f"mode started on {host}:{self.mode_port}")

        while True:
            print("mode")
            client_socket, client_address = server_socket.accept()
            print(f"mode Connection from {client_address}")
            self.handle_client_mode(client_socket)
            time.sleep(0.5)
            
    def handle_client_mode(self, client_socket):
        """处理 WebSocket 客户端连接"""
        global file_flag
        global file_start_flag
        # 握手过程
        self.websocket.handshake(client_socket)
        client_socket.setblocking(False)
        while True:
            try:
                message = self.websocket.receive(client_socket) 
                if message:
                    message = str(message)
                    if message == 'scratch':
                        file_flag = False
                        file_start_flag = False
                        self.websocket.send(client_socket,'success')
                        start_execution()
                        break
                    elif message == 'file':
                        file_flag = True
                        self.speaker_flag = False
                        self.websocket.send(client_socket,'success')
                        stop_execution()
                        break
                    elif message == 'stop':
                        self.scratch_stop = True
                        speaker.music_flag = False
                        rgb_sensor.line_flag = False
                        self.speaker_flag = False
                        print("stop")
                        break
                    else:
                        if file_start_flag:
                            self.websocket.send(client_socket,'failed')
                        else:
                            self.process_message(client_socket, message)
                            self.websocket.send(client_socket,'success')
                        break
            except OSError as e:
                # MicroPython 中非阻塞模式无数据时的错误码通常是 11 (EAGAIN)
                if e.args[0] == 11:  # 11 是 EAGAIN/EWOULDBLOCK 的常见错误码
                    continue
                else:
                    print(f"Socket 错误: {e}")
                    break
            except Exception as e:
                import sys
                print(f"Unexpected error: {e}, Type: {type(e)}")
                sys.print_exception(e)  # 显示完整的错误信息
                break
        gc.collect()
        # 关闭连接后清理资源
        client_socket.close()
        print("mode closed. Ready for a new client.")

    def start_speaker(self,host):
        """启动 WebSocket 设置服务器"""
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind((host, self.speak_port))
        server_socket.listen(1)  # 最大连接数为 1，只允许一个客户端连接
        print(f"start_speaker started on {host}:{self.speak_port}")

        while True:
            client_socket, client_address = server_socket.accept()
            print(f"start_speaker Connection from {client_address}")
            self.handle_client_speaker(client_socket)
            time.sleep(0.5)   
    def handle_client_speaker(self, client_socket):
        """处理 WebSocket 客户端连接"""
        global file_flag
        # 握手过程
        self.speaker_flag = True
        self.websocket.handshake(client_socket)
        client_socket.setblocking(False)
        last_received_time = time.ticks_ms()
        while self.speaker_flag:
            try:
                if time.ticks_ms() - last_received_time > 3000:
                    print("No data received for 3 seconds, disconnecting...")
                    break
                message = self.websocket.receive(client_socket) 
                if message:
                    last_received_time = time.ticks_ms()
                    if isinstance(message, bytes): 
                        esp_audio.music_play(bytearray(message)) # 使用封装的播放函数

            except OSError as e:
                # MicroPython 中非阻塞模式无数据时的错误码通常是 11 (EAGAIN)
                if e.args[0] == 11:  # 11 是 EAGAIN/EWOULDBLOCK 的常见错误码
                    continue
                else:
                    print(f"Socket 错误: {e}")
                    break
            except Exception as e:
                import sys
                print(f"Unexpected error: {e}, Type: {type(e)}")
                sys.print_exception(e)  # 显示完整的错误信息
                break

        # 关闭连接后清理资源
        client_socket.close()
        print("start_speaker closed. Ready for a new client.")  
    def process_message(self, ws, msg):
        """消息处理函数"""
        try:
            data = ujson.loads(msg)
            handler = self.cmd_handlers.get(data["command"], None)
            if handler:
                handler(ws, data)
        except Exception as e:
            print(e)
    def handle_camera(self, ws, data):
        """处理摄像头控制"""
        mode = data["params"]["mode"]
        num = data["params"]["num"]
        if mode == 0:
            camera.close()
        elif mode == 1:
            camera.web_open()
        elif mode == 2:
            camera.set_pixel(num)    
    def handle_micphone(self, ws, data):
        """处理麦克风控制"""
        status = data["params"]["status"]
        if status == 0:
            microphone.close()
        elif status == 1:
            microphone.open()            
    def handle_motor(self, ws, data):
        """处理电机控制"""
        mode = data["params"]["mode"]
        mytime = data["params"]["time"]
        mydistance = data["params"]["distance"]
        speed = max(0, min(100, data["params"]["speed"]))
        l_speed = max(-100, min(100, data["params"]["l_speed"]))
        r_speed = max(-100, min(100, data["params"]["r_speed"]))
        if mode == 1:
            motor.move_stop()
        elif mode == 2:
            motor.move_forward(speed, duration=mytime, distance=mydistance)
        elif mode == 3:
            motor.move_backward(speed, duration=mytime, distance=mydistance)
        elif mode == 4:
            motor.turn_left(speed, duration=mytime, distance=mydistance)
        elif mode == 5:
            motor.turn_right(speed, duration=mytime, distance=mydistance)
        elif mode == 6:
            motor.drive(l_speed, r_speed)
        elif mode == 7:
            motor.leftmotor_drive(speed, duration=mytime, distance=mydistance)
        elif mode == 8:
            motor.rightmotor_drive(speed, duration=mytime, distance=mydistance)  
    def handle_gripper(self, ws, data):
        """处理爪子控制"""
        port = data["params"]["port"]
        mode = data["params"]["mode"]
        if mode == 1:
            gripper.open(port)
        elif mode == 2:
            gripper.close(port)   
        elif mode == 3:
            gripper.open_until_done(port)  
        elif mode == 4:
            gripper.close_until_done(port)   
    def handle_gun(self, ws, data):
        """处理炮台控制"""
        port = data["params"]["port"]
        mode = data["params"]["mode"]
        num = data["params"]["num"]
        if mode == 1:
            gun.fire(port,num)
        elif mode == 2:
            gun.fire_until_done(port,num)    
    def handle_display(self, ws, data):
        """处理显示屏控制"""
        mode = data["params"]["mode"]
        lum = data["params"]["lum"]
        var = data["params"]["var"]
        image = data["params"]["image"]
        pos_x = data["params"]["pos_x"]
        pos_y = data["params"]["pos_y"] 
        num = data["params"]["num"] 
        way = data["params"]["way"] 
        if mode == 1:
            display.set_brightness(lum)
        elif mode == 2:
            display.show_image(image,way)
        elif mode == 3:
            display.show_text(var,way)
        elif mode == 4:
            display.show_expression(num)
        elif mode == 6:
            display.set_pixel(pos_x, pos_y)
        elif mode == 5:
            display.add_pixel(pos_x, pos_y)
        elif mode == 7:
            display.clear_pixel(pos_x, pos_y)
        elif mode == 8:
            display.toggle_pixel(pos_x, pos_y)
        elif mode == 9:
            display.clear()              
    def handle_speaker(self, ws, data):
        """处理音乐控制"""
        vol = data["params"]["vol"]
        name = data["params"]["name"]
        mode = data["params"]["mode"]

        if mode == 1:
            speaker.set_volume(vol)
        elif mode ==2:
            speaker.play_music_until_done(name)
        elif mode ==3:
            speaker.play_music(name)
        elif mode ==4:   
            speaker.stop_sounds()
    def handle_rgb_sensor(self, ws, data):
        """处理巡线控制"""
        num = data["params"]["num"]
        learn_color = data["params"]["learn_color"]
        mode = data["params"]["mode"]
        if mode == 1:
            rgb_sensor.start_grayscale_learning()
        elif mode == 2:
            rgb_sensor.start_color_learning(learn_color)  
        elif mode == 3:
            rgb_sensor.set_line_mode(num) 
        elif mode == 4:
            rgb_sensor.close()
    def handle_line_tracking(self, ws, data):
        """处理自动巡线"""
        mode = data["params"]["mode"]
        speed = data["params"]["speed"]
        line = data["params"]["line"]
        if mode == 1:
            rgb_sensor.line_flag = True
            rgb_sensor.line_tracking_until(speed,line)
        if mode == 2:
            rgb_sensor.line_tracking(speed)
        if mode == 3:
            rgb_sensor.stop_line_tracking()
    def update_ap(self, ws, data):
        """处理更改ap名称"""
        ssid = data["params"]["ssid"]
        gc.collect() 
        wifi.save_ap(ssid)
    def handle_upload_script(self, ws, data):
        """处理脚本下载"""
        name = data["params"]["name"]
        script = data["params"]["script"]
        if script:
            with open(name, 'w') as file:
                file.write(script)
            print(script)    
            print("脚本下载完成")

scratch = Scratch()

class usart_receive:
    def __init__(self):
        self.buf = bytearray(11)
        self.idx = 0

        self.reply = -1

        self.power_on = 0
        self.is_charging = 1
        self.power = 4

        self.lkey = 1
        self.rkey = 1
        self.privacy_switch = 1

        self.lmotor_mode = 0
        self.lmotor_speed = 0
        self.lmotor_distance = 0

        self.rmotor_mode = 0
        self.rmotor_speed = 0
        self.rmotor_distance = 0

        self.line_mode = 0
        self.line = [0,0,0,0,0]

        self.gripper_port = 0
        self.gripper_addr = 0
        self.gripper = 0

        self.gun_port = 0
        self.gun_addr = 0
        self.gun = 0
        self.gun_num = 0

    def receive(self):
        while True:
            while True:
                if uart.any():  # 判断接收缓冲区是否有数据
                    data = uart.read(1)  # 读取1字节数据
                    if data[0] == 0xAA:  # 如果包头正确
                        self.buf[0] = data[0]
                        self.idx = 1 # 将包头添加到数据列表
                        break  # 跳出循环开始接收数据部分
            while self.idx < 11:
                if uart.any():  # 判断接收缓冲区是否有数据
                    self.buf[self.idx] = uart.read(1)[0] # 读取1字节数据
                    self.idx += 1
            if self.buf[10] == 0xBB :
                self.parse_packet()
                self.idx = 0 
    def parse_packet(self):
        """解析预存缓冲区数据"""
        if self.buf[2] == 0:
            self.power_on = self.buf[3]
            self.is_charging = self.buf[4]
            self.power = self.buf[5]
        elif self.buf[2] == 1:
            self.lkey = self.buf[3]
            self.rkey = self.buf[4]
            self.privacy_switch = self.buf[5]
        elif self.buf[2] == 2:
            self.lmotor_mode = self.buf[3]
            self.lmotor_speed = (self.buf[4] << 8) | self.buf[5]
            self.lmotor_distance = (self.buf[6] << 8) | self.buf[7]
        elif self.buf[2] == 3:
            self.rmotor_mode = self.buf[3]
            self.rmotor_speed = (self.buf[4] << 8) | self.buf[5]
            self.rmotor_distance = (self.buf[6] << 8) | self.buf[7]
        elif self.buf[2] == 4:
            self.line_mode = self.buf[3]
            self.line = self.buf[4:9]
        elif self.buf[2] == 5:
            self.gripper_port = self.buf[3]
            self.gripper_addr = self.buf[4]
            self.gripper = self.buf[5]
        elif self.buf[2] == 6:
            self.gun_port = self.buf[3]
            self.gun_addr = self.buf[4]
            self.gun = self.buf[5]
            self.gun_num = self.buf[6]
        elif self.buf[2] == 0xf0:
            self.reply = 1
        elif self.buf[2] == 0xf1:
            self.reply = 0
uart_receive = usart_receive()

def start_receive():
    _thread.start_new_thread(uart_receive.receive,())
