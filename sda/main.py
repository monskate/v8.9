import icrobot
import time
import _thread
import gc
from machine import Pin
import module
import esp_audio

timeout = 10  # 设定10秒的超时时间
last_pressed_time = None  # 记录按键按下的时间
power = Pin(5, Pin.IN, Pin.PULL_UP)
start = False
file_id = None
def execute_file(filename):
    with open(filename, 'r') as file:
        code = file.read()
    icrobot.start_execution()
    time.sleep_ms(100)
    exec(code, globals())

def power_callback(pin):
    if power.value() == 0:
        icrobot.file_start_flag = not icrobot.file_start_flag
        print(icrobot.file_start_flag)
        
if __name__ == '__main__':
    gc.enable()
    icrobot.start_receive()
    power.irq(trigger=Pin.IRQ_FALLING, handler=power_callback)
    with open("/flash/key.wav", 'rb') as f:
        f.seek(1024)  # 跳过 WAV 文件头部，直接读取音频数据     
        key = f.read()
    icrobot.camera.open()
    icrobot.ai.set_model(icrobot..qr_recognition)
    
    icrobot.speaker.play_music_until_done("/music/distribution_network.wav")
    start_scan_time = time.ticks_ms()  # 记录扫描开始时间
    
    while True:
        if time.ticks_diff(time.ticks_ms(), start_scan_time) > 10000:  # 超过10秒
            print("10秒内未扫描到 WiFi 二维码，退出扫描。")
            icrobot.ai.close_model()
            icrobot.camera.close()
            break
        
        if icrobot.ai.qr_isrecognized and icrobot.ai.get_qr_information():
            qr_data = icrobot.ai.get_qr_information()

            if qr_data.startswith("WIFI:"):
                icrobot.speaker.play_music("/music/saomadi.wav")
                try:
                    wifi_info = qr_data[5:-2]  # 去掉 "WIFI:" 和 结尾的 ";;"
                    wifi_dict = dict(item.split(":") for item in wifi_info.split(";") if ":" in item)

                    ssid = wifi_dict.get("S", "")
                    password = wifi_dict.get("P", "")
                    if ssid:
                        if not icrobot.wifi.sta.active():
                            icrobot.wifi.sta.active(True)
                        icrobot.wifi.sta.connect(ssid, password)
                        print(f"尝试连接: {ssid}, {password}")
                        
                        start_time = time.ticks_ms()  # 记录WiFi连接开始时间
                        while not icrobot.wifi.sta.isconnected():
                            if time.ticks_diff(time.ticks_ms(), start_time) > 5000:  # 连接超时
                                print("WiFi 连接超时，重新扫描二维码...")
                                break  # 重新扫描

                        if icrobot.wifi.sta.isconnected():  # 连接成功才播放提示音
                            print("WiFi 连接成功！")
                            icrobot.ai.close_model()
                            icrobot.camera.close()
                            icrobot.speaker.play_music("/music/connection_successful.wav")
                            break  # 连接成功，退出函数

                except Exception as e:
                    print("error:", e)
    host = icrobot.wifi.information()[0]
    icrobot.video_start(host)
    _thread.start_new_thread(icrobot.scratch.start_receive,(host,),7*1024)
    _thread.start_new_thread(icrobot.scratch.start_send, (host,),4*1024)
    _thread.start_new_thread(icrobot.scratch.start_mode, (host,),4*1024)
    _thread.start_new_thread(icrobot.scratch.start_speaker, (host,),4*1024)
    while True:
        gc.collect()
        if icrobot.file_flag:
            if not start:
                if icrobot.leftkey.value() == 0:
                    esp_audio.music_play(bytearray(key))
                    while icrobot.leftkey.value() == 0:
                        pass
                    icrobot.file_num = icrobot.file_num + 1
                    if icrobot.file_num > 5:
                        icrobot.file_num = 1
                    icrobot.power.set_status(icrobot.file_num)
                    last_pressed_time = time.time()
                if icrobot.rightkey.value() == 0:
                    esp_audio.music_play(bytearray(key))
                    while icrobot.rightkey.value() == 0:
                        pass
                    icrobot.file_num = icrobot.file_num - 1
                    if icrobot.file_num < 1:
                        icrobot.file_num = 5
                    icrobot.power.set_status(icrobot.file_num)
                    last_pressed_time = time.time()
                if last_pressed_time and time.time() - last_pressed_time >= timeout:
                    # 如果没有进入 `file_start_flag` 判断，就显示另一个表情
                    if not icrobot.file_start_flag:
                        print("超时，切换表情")
                        icrobot.file_num = 0
                        icrobot.power.set_status(255)
                    # 重置 last_pressed_time，防止每次循环都进入超时判断
                    last_pressed_time = None
            if icrobot.file_start_flag and not start: 
                if icrobot.file_num == 0:
                    icrobot.file_start_flag = False
                    continue
                file_path = icrobot.file_path[icrobot.file_num-1]
                file_id = _thread.start_new_thread(execute_file, (file_path,),8*1024)
                print("执行脚本",file_id)
                start = True
            if not icrobot.file_start_flag and start: 
                icrobot.speaker.music_flag = False
                icrobot.rgb_sensor.line_flag = False
                icrobot.ai.ai_start = False
                print("脚本退出",file_id)
                _thread.delete(file_id)
                file_id = None
                last_pressed_time = None  # 记录按键按下的时间
                icrobot.stop_execution()
                icrobot.file_start_flag = False
                start = False
        time.sleep(0.2)

