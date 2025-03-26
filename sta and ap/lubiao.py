import time
import uos
import esp_camera
from machine import Pin,
from microdot import Microdot
import _thread
import esp_audio
import w25qxx
import icrobot
road_result = -1
"""
1：速度80，2：速度100，3：左转，4：右转，5：停止，6：喇叭，7：绿灯
"""
start = False
road_flag = False

icrobot.file_start_flag = True
# CORS头信息
CORS_HEADERS = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type'
}

BaseSpeed = 45

Kp = 0.12
Kd = 0.06
dall = 0
RSpeed = 0
LSpeed = 0
lasterror = 0
Motor = 0
error = 0
def video_stream_task():
    app = Microdot()
    # 定义视频流的路由
    @app.route('/video_feed', methods=['GET', 'OPTIONS'])
    def video_feed(request):
        def stream():
            yield b'--frame\r\n'
            while True:
                frame = esp_camera.capture()
                yield b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n--frame\r\n'
                time.sleep_ms(50)
        
        return stream(), 200, {
            'Content-Type': 'multipart/x-mixed-replace; boundary=frame',
            'Access-Control-Allow-Origin': '*'
        }

    # 启动视频流的Microdot应用
    app.run(host = "192.168.4.1",port=8081, debug=True)  # 将视频流放在8081端口上
# 处理指令请求的函数
def command_task():
    app = Microdot()

    @app.route('/roadsign_recognition', methods=['GET', 'POST', 'OPTIONS'])
    def receive_num(request):
        global road_result
        global speed
        if request.method == 'OPTIONS':
            return '', 204, CORS_HEADERS
        data = request.json.get('data')
        if data is not None:
            if data == '60':
                road_result = 1
                print(80)
            elif data == '80':
                road_result = 2
                print(100)
            elif data == 'left':
                road_result = 3
                print("左转")
            elif data == 'right':
                road_result = 4
                print("右转")
            elif data == 'stop':
                road_result = 5
                print("停车") 
            elif data == 'whistle':
                road_result = 6
                print("喇叭")
            elif data == 'green':
                road_result = 7
                print("绿灯")
            elif data == 'target':
                road_result = 8
                print("发射")
            return {'status': 'success', 'message': 'data'}, 200, CORS_HEADERS
        else:
            return {'status': 'error', 'message': '无data'}, 400, CORS_HEADERS
    
    # 启动指令处理的Microdot应用
    app.run(host = "192.168.4.1",port=8080, debug=True)  # 主应用在80端口上
    
def read_wav(filename,header):
    with open(filename, 'rb') as f:
        header = f.read(header) 
        return f.read()
# 主程序入口
if __name__ == '__main__':
    icrobot.start_receive()
    power = Pin(5, Pin.IN, Pin.PULL_UP)
    car = read_wav("/flash/car.wav",1024)
    icrobot.wifi.ap.active(True)
    icrobot.wifi.ap.config(essid=icrobot.wifi.default_ap_ssid,max_clients=1)
    # 启动视频流任务
    icrobot.camera.web_open()
    _thread.start_new_thread(video_stream_task, (),10*1024)
    # 启动指令处理任务
    _thread.start_new_thread(command_task, (),10*1024)
    while True:
        if power.value() == 0 :            
            start = not start
            icrobot.rgb_sensor.set_line_mode(2)
            time.sleep_ms(10)
            while power.value() == 0:
                time.sleep(0.01)  # 等待按键释放
        if start :
            gry_val = icrobot.uart_receive.line
            if gry_val:
                print(gry_val)
                if gry_val[0]<120 and gry_val[1]<120 and gry_val[2]<120 and gry_val[3]<120 and gry_val[4]<120 :
                    icrobot.motor.move_stop()
                    start = False
                    time.sleep_ms(500)
                    road_flag = True
                else:
                    error = gry_val[4]*2.3+gry_val[3]-gry_val[1]-gry_val[0]*2.3
                    dall = error-lasterror
                    
                    Motor = Kp*error + dall*Kd
                    LSpeed = BaseSpeed - Motor
                    RSpeed = BaseSpeed + Motor
                    lasterror = error
                    icrobot.motor.drive(int(LSpeed+5), int(RSpeed))
        if not start and road_flag:
            if road_result==1:
                BaseSpeed = 35
                dall = 0
                RSpeed = 0
                LSpeed = 0
                lasterror = 0
                Motor = 0
                error = 0
                road_result = -1
                icrobot.motor.drive(BaseSpeed,BaseSpeed)
                time.sleep_ms(500)
                road_flag = False
                start =True
            elif road_result==2:
                BaseSpeed = 45
                dall = 0
                RSpeed = 0
                LSpeed = 0
                lasterror = 0
                Motor = 0
                error = 0
                icrobot.motor.drive(BaseSpeed,BaseSpeed)
                time.sleep_ms(200)
                road_flag = False
                start =True
            elif road_result==3:#左转
                speed = 35
                dall = 0
                RSpeed = 0
                LSpeed = 0
                lasterror = 0
                Motor = 0
                error = 0
                road_result = -1
                icrobot.motor.drive(35, 35)
                time.sleep_ms(200)
                icrobot.motor.turn_left(50)
                time.sleep(0.9)
                while True: 
                    gry_val = icrobot.uart_receive.line
                    if gry_val:
                        print(gry_val)
                        if gry_val[0]<120 and gry_val[1]<120 and gry_val[2]<120 and gry_val[3]<120 and gry_val[4]<120 :
                            icrobot.motor.move_stop()
                            start = False
                            time.sleep_ms(100)
                            road_flag = True
                        if gry_val[0]<120 and gry_val[1]<120 and gry_val[2]<100 and gry_val[4]>230:
                            icrobot.motor.drive(35, 35)
                            time.sleep_ms(200)
                            icrobot.motor.turn_left(50)
                            time.sleep(0.9)
                            start = True
                            break
                        else:
                            error = gry_val[4]*1.5+gry_val[3]-gry_val[1]-gry_val[0]*1.5
                            dall = error-lasterror
                            
                            Motor = Kp*error + dall*Kd
                            LSpeed = speed - Motor
                            RSpeed = speed + Motor
                            lasterror = error
                            icrobot.motor.drive(int(LSpeed), int(RSpeed))
                           
            elif road_result==4:#右转
                speed = 35
                dall = 0
                RSpeed = 0
                LSpeed = 0
                lasterror = 0
                Motor = 0
                error = 0
                road_result = -1
                icrobot.motor.drive(35, 35)
                time.sleep_ms(200)
                icrobot.motor.turn_right(50)
                time.sleep(0.9)
                while True: 
                    gry_val = icrobot.uart_receive.line
                    if gry_val:
                        print(gry_val)
                        if gry_val[0]<120 and gry_val[1]<120 and gry_val[2]<120 and gry_val[3]<120 and gry_val[4]<120 :
                            icrobot.motor.move_stop()
                            start = False
                            time.sleep_ms(100)
                            road_flag = True
                        if gry_val[2]<100 and gry_val[3]<100 and gry_val[4]<100 and gry_val[0]>230 :
                            icrobot.motor.drive(35, 35)
                            time.sleep_ms(200)
                            icrobot.motor.turn_right(50)
                            time.sleep(0.9)
                            start = True
                            break
                        else:
                            error = gry_val[4]*1.5+gry_val[3]-gry_val[1]-gry_val[0]*1.5
                            dall = error-lasterror
                            
                            Motor = Kp*error + dall*Kd
                            LSpeed = speed - Motor
                            RSpeed = speed + Motor
                            lasterror = error
                            icrobot.motor.drive(int(LSpeed), int(RSpeed))
            elif road_result==5:#倒车入库
                icrobot.motor.turn_left(50)
                time.sleep(0.9)
                icrobot.motor.move_backward(50,distance=250)
                icrobot.motor.move_stop()
                road_result = -1
                icrobot.rgb_sensor.close()
                road_flag = False
            elif road_result==6:
                dall = 0
                RSpeed = 0
                LSpeed = 0
                lasterror = 0
                Motor = 0
                error = 0
                esp_audio.music_play(bytearray(car))
                road_result = -1
                icrobot.motor.drive(BaseSpeed,BaseSpeed)
                time.sleep_ms(200)
                road_flag = False
                start =True
                            
            elif road_result==7:
                dall = 0
                RSpeed = 0
                LSpeed = 0
                lasterror = 0
                Motor = 0
                error = 0
                road_result = -1
                icrobot.motor.drive(BaseSpeed,BaseSpeed)
                time.sleep_ms(200)
                road_flag = False
                start =True


